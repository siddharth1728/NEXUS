import pytest
import random
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, UserSkill, Gap, SkillState
from app.models.profile import StudentProfile
from app.models.taxonomy import TargetRole, Skill
from app.models.project import Project, RepositorySnapshot, Artifact, RawObservation, Evidence, EvidenceType, EvidenceSkill, SnapshotStatus
from app.models.ecosystem import (
    MentorRelationship, MentorNote, ReviewLink,
    Cohort, CohortMembership, Team, TeamMember, TeamProject, SharingAuditLog,
    RelationshipStatus
)
from app.core.security import create_access_token

def clean_state(db, user_id):
    db.query(MentorNote).filter(MentorNote.student_id == user_id).delete(synchronize_session=False)
    db.query(MentorRelationship).filter(MentorRelationship.student_id == user_id).delete(synchronize_session=False)
    db.query(ReviewLink).filter(ReviewLink.student_id == user_id).delete(synchronize_session=False)
    db.query(CohortMembership).filter(CohortMembership.student_id == user_id).delete(synchronize_session=False)
    db.query(TeamMember).filter(TeamMember.user_id == user_id).delete(synchronize_session=False)
    db.query(SharingAuditLog).filter(SharingAuditLog.resource_owner_id == user_id).delete(synchronize_session=False)
    db.query(Gap).filter(Gap.user_id == user_id).delete(synchronize_session=False)
    db.query(UserSkill).filter(UserSkill.user_id == user_id).delete(synchronize_session=False)
    db.commit()

# 1. Mentor invitation & permissions
def test_mentor_invitation_flow(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    res = auth_client.post(
        "/api/ecosystem/mentor/invite",
        json={"mentor_email": "mentor@advising.test", "permissions": ["PROFILE", "PROJECTS", "LAB", "CLAIMS"], "expires_in_days": 14}
    )
    assert res.status_code == 201
    data = res.json()
    assert data["invite_token"]
    assert "LAB" in data["permissions"]
    assert "CLAIMS" in data["permissions"]

# 2. Invitation expiration
def test_mentor_invitation_expiration(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    res = auth_client.post("/api/ecosystem/mentor/invite", json={"permissions": ["PROFILE"], "expires_in_days": 1})
    token = res.json()["invite_token"]
    
    # Fast forward expiration in DB
    rel = db_session.query(MentorRelationship).filter(MentorRelationship.invite_token == token).first()
    rel.expires_at = datetime.now(timezone.utc) - timedelta(days=2)
    db_session.commit()

    mentor_user = User(email=f"exp_mentor_{random.randint(10000, 99999)}@test.com", password_hash="hash")
    db_session.add(mentor_user)
    db_session.commit()
    t_m = create_access_token(mentor_user.id)
    c_m = TestClient(app)
    c_m.cookies.set("access_token", t_m)

    res_acc = c_m.post("/api/ecosystem/mentor/accept", json={"invite_token": token})
    assert res_acc.status_code == 400
    assert "expired" in res_acc.json()["detail"].lower()

# 3. Invitation single-use & acceptance
def test_mentor_invitation_single_use(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    res = auth_client.post("/api/ecosystem/mentor/invite", json={"permissions": ["PROFILE"]})
    token = res.json()["invite_token"]

    mentor_1 = User(email=f"mentor_1_{random.randint(10000, 99999)}@test.com", password_hash="hash")
    mentor_2 = User(email=f"mentor_2_{random.randint(10000, 99999)}@test.com", password_hash="hash")
    db_session.add_all([mentor_1, mentor_2])
    db_session.commit()

    c1 = TestClient(app)
    c1.cookies.set("access_token", create_access_token(mentor_1.id))
    assert c1.post("/api/ecosystem/mentor/accept", json={"invite_token": token}).status_code == 200

    # Second acceptance must fail
    c2 = TestClient(app)
    c2.cookies.set("access_token", create_access_token(mentor_2.id))
    res2 = c2.post("/api/ecosystem/mentor/accept", json={"invite_token": token})
    assert res2.status_code == 400
    assert "already been accepted" in res2.json()["detail"].lower()

# 4. Mentor permissions scope enforcement
def test_mentor_scoped_dossier_filtering(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    p = Project(user_id=test_user.id, github_repo_id=random.randint(100000, 999999), name="ScopeTestRepo", is_public=False)
    db_session.add(p)
    db_session.commit()

    res_inv = auth_client.post("/api/ecosystem/mentor/invite", json={"permissions": ["PROFILE", "PROJECTS"]})
    token = res_inv.json()["invite_token"]

    m = User(email=f"scoped_mentor_{random.randint(10000, 99999)}@test.com", password_hash="hash")
    db_session.add(m)
    db_session.commit()
    c = TestClient(app)
    c.cookies.set("access_token", create_access_token(m.id))
    c.post("/api/ecosystem/mentor/accept", json={"invite_token": token})

    res_dos = c.get(f"/api/ecosystem/mentor/students/{test_user.id}")
    assert res_dos.status_code == 200
    dossier = res_dos.json()
    assert dossier["verified_proof"] is None  # PROOF scope omitted
    assert dossier["active_quests"] is None   # QUESTS scope omitted
    assert len(dossier["featured_projects"]) >= 1

# 5. Immediate mentor revocation
def test_immediate_mentor_revocation_lockout(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    m = User(email=f"rev_m_{random.randint(10000, 99999)}@test.com", password_hash="hash")
    db_session.add(m)
    db_session.commit()
    c = TestClient(app)
    c.cookies.set("access_token", create_access_token(m.id))

    res_inv = auth_client.post("/api/ecosystem/mentor/invite", json={"permissions": ["PROFILE"]})
    c.post("/api/ecosystem/mentor/accept", json={"invite_token": res_inv.json()["invite_token"]})
    assert c.get(f"/api/ecosystem/mentor/students/{test_user.id}").status_code == 200

    # Revoke
    auth_client.post(f"/api/ecosystem/mentor/revoke/{res_inv.json()['relationship_id']}")

    # Immediate 403
    assert c.get(f"/api/ecosystem/mentor/students/{test_user.id}").status_code == 403

# 6. Mentor notes creation & isolation
def test_mentor_notes_truth_isolation(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    s_db = db_session.query(Skill).filter(Skill.name == "PostgreSQL").first()
    if not s_db:
        s_db = Skill(name="PostgreSQL", category="Database")
        db_session.add(s_db)
        db_session.commit()

    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_db.id, state=SkillState.DEVELOPING, calculation_version="v1"))
    db_session.add(Gap(user_id=test_user.id, skill_id=s_db.id, actual_state="DEVELOPING", required_state="STRONG", state_distance=1, importance_weight=1.0, severity=2, calculation_version="v1"))
    db_session.commit()

    m = User(email=f"note_m_{random.randint(10000, 99999)}@test.com", password_hash="hash")
    db_session.add(m)
    db_session.commit()
    c = TestClient(app)
    c.cookies.set("access_token", create_access_token(m.id))

    res_inv = auth_client.post("/api/ecosystem/mentor/invite", json={"permissions": ["PROFILE", "QUESTS"]})
    c.post("/api/ecosystem/mentor/accept", json={"invite_token": res_inv.json()["invite_token"]})

    res_note = c.post(
        f"/api/ecosystem/mentor/students/{test_user.id}/notes",
        json={"note_text": "Suggest index tuning on user table.", "recommended_concept_key": "db_indexing"}
    )
    assert res_note.status_code == 201

    # Verify deterministic states unchanged
    us = db_session.query(UserSkill).filter(UserSkill.user_id == test_user.id, UserSkill.skill_id == s_db.id).first()
    assert us.state == SkillState.DEVELOPING
    gap = db_session.query(Gap).filter(Gap.user_id == test_user.id, Gap.skill_id == s_db.id).first()
    assert gap is not None  # Gap still open (mentor note is guidance, NOT evidence)

# 7. Project review links & expiration
def test_review_links_lifecycle(auth_client, client, db_session, test_user):
    clean_state(db_session, test_user.id)
    p = Project(user_id=test_user.id, github_repo_id=random.randint(100000, 999999), name="ReviewApp", is_public=False)
    db_session.add(p)
    db_session.commit()

    res_link = auth_client.post("/api/ecosystem/review-links", json={"project_id": p.id, "label": "TechScreen", "expires_in_days": 7})
    assert res_link.status_code == 201
    token = res_link.json()["token"]
    link_id = res_link.json()["id"]

    # Public access
    res_pub = client.get(f"/api/ecosystem/review/{token}")
    assert res_pub.status_code == 200
    assert res_pub.json()["project_name"] == "ReviewApp"
    assert "questions_to_explore" in res_pub.json()

    # Revocation
    auth_client.post(f"/api/ecosystem/review-links/revoke/{link_id}")
    assert client.get(f"/api/ecosystem/review/{token}").status_code == 404

# 8. Educator observatory & anti-identification
def test_educator_observatory_thresholds_and_anti_identification(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    res_c = auth_client.post("/api/ecosystem/educator/cohorts", json={"name": "DevOps 101", "course_code": "DO-101"})
    cohort_id = res_c.json()["id"]
    invite_code = res_c.json()["invite_code"]

    # 1. < 3 students -> UNAVAILABLE
    res_under = auth_client.get(f"/api/ecosystem/educator/cohorts/{cohort_id}/analytics")
    assert res_under.json()["privacy_status"] == "UNAVAILABLE_INSUFFICIENT_SIZE"

    # 2. Add 3 students
    s_k8s = db_session.query(Skill).filter(Skill.name == "Kubernetes").first()
    if not s_k8s:
        s_k8s = Skill(name="Kubernetes", category="Infra")
        db_session.add(s_k8s)
        db_session.commit()

    students = []
    for i in range(3):
        u = User(email=f"c_stu_{i}_{random.randint(100,999)}@test.com", password_hash="hash")
        db_session.add(u)
        students.append(u)
    db_session.commit()

    # Give only 1 student the Kubernetes skill
    db_session.add(UserSkill(user_id=students[0].id, skill_id=s_k8s.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.commit()

    for s in students:
        c = TestClient(app)
        c.cookies.set("access_token", create_access_token(s.id))
        c.post("/api/ecosystem/educator/cohorts/join", json={"invite_code": invite_code})

    # 3. 3 students -> LIMITED_SUMMARY + Anti-Identification suppression
    res_lim = auth_client.get(f"/api/ecosystem/educator/cohorts/{cohort_id}/analytics")
    assert res_lim.json()["privacy_status"] == "LIMITED_SUMMARY"
    
    # Kubernetes held by 1 student must be suppressed
    sig_k8s = next((s for s in res_lim.json()["most_common_signals"] if s["name"] == "Kubernetes"), None)
    assert sig_k8s is not None
    assert sig_k8s["frequency"] == "INSUFFICIENT COHORT SIZE FOR THIS SIGNAL"

# 9. Team project sharing and member removal
def test_team_project_isolation_and_member_removal(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    p_shared = Project(user_id=test_user.id, github_repo_id=random.randint(100000, 999999), name="SharedTeamService", is_public=False)
    p_secret = Project(user_id=test_user.id, github_repo_id=random.randint(100000, 999999), name="SecretPersonalProject", is_public=False)
    db_session.add_all([p_shared, p_secret])
    db_session.commit()

    res_t = auth_client.post("/api/ecosystem/teams", json={"name": "Core Platform"})
    team_id = res_t.json()["team_id"]
    invite_code = res_t.json()["invite_code"]

    auth_client.post(f"/api/ecosystem/teams/{team_id}/share-project", json={"project_id": p_shared.id})

    # Member joins
    member = User(email=f"teammate_{random.randint(10000, 99999)}@test.com", password_hash="hash")
    db_session.add(member)
    db_session.commit()
    c_m = TestClient(app)
    c_m.cookies.set("access_token", create_access_token(member.id))
    c_m.post("/api/ecosystem/teams/join", json={"invite_code": invite_code})

    # Member sees shared project, not secret project
    res_collab = c_m.get(f"/api/ecosystem/teams/{team_id}/collaboration")
    assert res_collab.status_code == 200
    shared_names = [p["name"] for p in res_collab.json()["shared_projects"]]
    assert "SharedTeamService" in shared_names
    assert "SecretPersonalProject" not in shared_names

    # Lead removes member
    res_rem = auth_client.post(f"/api/ecosystem/teams/{team_id}/remove-member/{member.id}")
    assert res_rem.status_code == 200

    # Removed member immediately receives 403
    assert c_m.get(f"/api/ecosystem/teams/{team_id}/collaboration").status_code == 403

# 10. Sharing center overview & audience preview
def test_sharing_center_and_audience_previews(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    res_ov = auth_client.get("/api/ecosystem/sharing")
    assert res_ov.status_code == 200
    assert "permissions_ledger" in res_ov.json()

    # Previews
    res_prev_pub = auth_client.get("/api/ecosystem/sharing/preview/PUBLIC")
    assert res_prev_pub.status_code == 200

    res_prev_m = auth_client.get("/api/ecosystem/sharing/preview/MENTOR")
    assert res_prev_m.status_code == 200
    assert res_prev_m.json()["audience"] == "MENTOR"
