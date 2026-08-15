import pytest
import random
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
    db.query(EvidenceSkill).filter(EvidenceSkill.evidence_id.in_(
        db.query(Evidence.id).filter(Evidence.raw_observation_id.in_(
            db.query(RawObservation.id).filter(RawObservation.artifact_id.in_(
                db.query(Artifact.id).filter(Artifact.snapshot_id.in_(
                    db.query(RepositorySnapshot.id).filter(RepositorySnapshot.project_id.in_(
                        db.query(Project.id).filter(Project.user_id == user_id)
                    ))
                ))
            ))
        ))
    )).delete(synchronize_session=False)
    db.query(Evidence).filter(Evidence.raw_observation_id.in_(
        db.query(RawObservation.id).filter(RawObservation.artifact_id.in_(
            db.query(Artifact.id).filter(Artifact.snapshot_id.in_(
                db.query(RepositorySnapshot.id).filter(RepositorySnapshot.project_id.in_(
                    db.query(Project.id).filter(Project.user_id == user_id)
                ))
            ))
        ))
    )).delete(synchronize_session=False)
    db.query(RawObservation).filter(RawObservation.artifact_id.in_(
        db.query(Artifact.id).filter(Artifact.snapshot_id.in_(
            db.query(RepositorySnapshot.id).filter(RepositorySnapshot.project_id.in_(
                db.query(Project.id).filter(Project.user_id == user_id)
            ))
        ))
    )).delete(synchronize_session=False)
    db.query(Artifact).filter(Artifact.snapshot_id.in_(
        db.query(RepositorySnapshot.id).filter(RepositorySnapshot.project_id.in_(
            db.query(Project.id).filter(Project.user_id == user_id)
        ))
    )).delete(synchronize_session=False)
    db.query(RepositorySnapshot).filter(RepositorySnapshot.project_id.in_(
        db.query(Project.id).filter(Project.user_id == user_id)
    )).delete(synchronize_session=False)
    db.query(Project).filter(Project.user_id == user_id).delete(synchronize_session=False)
    db.query(Gap).filter(Gap.user_id == user_id).delete(synchronize_session=False)
    db.query(UserSkill).filter(UserSkill.user_id == user_id).delete(synchronize_session=False)
    db.commit()

def test_mentor_invitation_and_scoped_dossier(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    # Setup skills and evidence for test_user
    s_py = db_session.query(Skill).filter(Skill.name == "Python").first()
    if not s_py:
        s_py = Skill(name="Python", category="Language")
        db_session.add(s_py)
        db_session.commit()

    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_py.id, state=SkillState.STRONG, calculation_version="v1"))
    
    p = Project(user_id=test_user.id, github_repo_id=random.randint(100000, 999999), name="MentorTestRepo", is_public=False)
    db_session.add(p)
    db_session.commit()

    # 1. Student creates invite omitting "PROOF" permission
    res_inv = auth_client.post(
        "/api/ecosystem/mentor/invite",
        json={
            "mentor_email": "mentor@advising.test",
            "permissions": ["PROFILE", "PROJECTS", "JOURNEY", "QUESTS"],
            "expires_in_days": 30
        }
    )
    assert res_inv.status_code == 201
    data_inv = res_inv.json()
    token = data_inv["invite_token"]
    assert "PROOF" not in data_inv["permissions"]

    # 2. Mentor accepts invite
    mentor_user = User(email="mentor_actual@advising.test", password_hash="hash")
    db_session.add(mentor_user)
    db_session.commit()
    token_mentor = create_access_token(mentor_user.id)

    client_m = TestClient(app)
    client_m.cookies.set("access_token", token_mentor)

    res_acc = client_m.post(
        "/api/ecosystem/mentor/accept",
        json={"invite_token": token}
    )
    assert res_acc.status_code == 200

    # 3. Mentor views student dossier
    res_dos = client_m.get(f"/api/ecosystem/mentor/students/{test_user.id}")
    assert res_dos.status_code == 200
    dossier = res_dos.json()
    assert dossier["student_id"] == test_user.id
    assert "PROJECTS" in dossier["granted_permissions"]
    assert dossier["verified_proof"] is None  # Strictly filtered: PROOF was not granted!
    assert len(dossier["featured_projects"]) >= 1

def test_immediate_mentor_revocation(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    mentor_user = User(email="mentor_revoketest@test.com", password_hash="hash")
    db_session.add(mentor_user)
    db_session.commit()
    token_mentor = create_access_token(mentor_user.id)

    client_m = TestClient(app)
    client_m.cookies.set("access_token", token_mentor)

    # Student invites and mentor accepts
    res_inv = auth_client.post("/api/ecosystem/mentor/invite", json={"permissions": ["PROFILE"]})
    token = res_inv.json()["invite_token"]
    rel_id = res_inv.json()["relationship_id"]

    client_m.post("/api/ecosystem/mentor/accept", json={"invite_token": token})

    # Verify mentor can read dossier
    assert client_m.get(f"/api/ecosystem/mentor/students/{test_user.id}").status_code == 200

    # Student immediately revokes access
    res_rev = auth_client.post(f"/api/ecosystem/mentor/revoke/{rel_id}")
    assert res_rev.status_code == 200

    # Mentor immediately receives 403 Forbidden
    res_denied = client_m.get(f"/api/ecosystem/mentor/students/{test_user.id}")
    assert res_denied.status_code == 403

def test_mentor_notes_isolation(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    s_test = db_session.query(Skill).filter(Skill.name == "Testing").first()
    if not s_test:
        s_test = Skill(name="Testing", category="Quality")
        db_session.add(s_test)
        db_session.commit()

    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_test.id, state=SkillState.DEVELOPING, calculation_version="v1"))
    db_session.commit()

    mentor_user = User(email="mentor_notetest@test.com", password_hash="hash")
    db_session.add(mentor_user)
    db_session.commit()
    token_m = create_access_token(mentor_user.id)
    client_m = TestClient(app)
    client_m.cookies.set("access_token", token_m)

    res_inv = auth_client.post("/api/ecosystem/mentor/invite", json={"permissions": ["PROFILE", "QUESTS"]})
    client_m.post("/api/ecosystem/mentor/accept", json={"invite_token": res_inv.json()["invite_token"]})

    # Mentor adds note recommending testing
    res_note = client_m.post(
        f"/api/ecosystem/mentor/students/{test_user.id}/notes",
        json={"note_text": "Consider adding pytest fixtures for integration tests."}
    )
    assert res_note.status_code == 201

    # Deterministic check: UserSkill state MUST NOT change
    us = db_session.query(UserSkill).filter(UserSkill.user_id == test_user.id, UserSkill.skill_id == s_test.id).first()
    assert us.state == SkillState.DEVELOPING  # Still DEVELOPING (mentor opinion is NOT evidence)

def test_project_review_links_and_public_access(auth_client, client, db_session, test_user):
    clean_state(db_session, test_user.id)

    p = Project(user_id=test_user.id, github_repo_id=random.randint(100000, 999999), name="ReviewableService", is_public=False)
    db_session.add(p)
    db_session.commit()

    # Create temporary review link
    res_link = auth_client.post(
        "/api/ecosystem/review-links",
        json={"project_id": p.id, "label": "Interviewer Screen", "expires_in_days": 7}
    )
    assert res_link.status_code == 201
    data_link = res_link.json()
    token = data_link["token"]

    # Anonymous public reviewer visits /api/ecosystem/review/{token}
    res_view = client.get(f"/api/ecosystem/review/{token}")
    assert res_view.status_code == 200
    review_data = res_view.json()
    assert review_data["project_name"] == "ReviewableService"
    assert len(review_data["questions_to_explore"]) >= 1

    # Student revokes review link
    res_rev = auth_client.post(f"/api/ecosystem/review-links/revoke/{data_link['id']}")
    assert res_rev.status_code == 200

    # Public reviewer receives 404
    assert client.get(f"/api/ecosystem/review/{token}").status_code == 404

def test_educator_observatory_privacy_thresholds(auth_client, client, db_session, test_user):
    clean_state(db_session, test_user.id)

    # 1. Educator creates cohort
    res_cohort = auth_client.post(
        "/api/ecosystem/educator/cohorts",
        json={"name": "Cloud Systems", "course_code": "CS-401"}
    )
    assert res_cohort.status_code == 201
    cohort_id = res_cohort.json()["id"]
    invite_code = res_cohort.json()["invite_code"]

    # Less than 3 students: UNAVAILABLE_INSUFFICIENT_SIZE
    res_analytics = auth_client.get(f"/api/ecosystem/educator/cohorts/{cohort_id}/analytics")
    assert res_analytics.status_code == 200
    assert res_analytics.json()["privacy_status"] == "UNAVAILABLE_INSUFFICIENT_SIZE"

    # Add 3 students: LIMITED_SUMMARY
    students = []
    for i in range(3):
        u = User(email=f"student_{i}_{random.randint(100,999)}@test.com", password_hash="hash")
        db_session.add(u)
        students.append(u)
    db_session.commit()

    for s in students:
        t = create_access_token(s.id)
        c = TestClient(app)
        c.cookies.set("access_token", t)
        c.post("/api/ecosystem/educator/cohorts/join", json={"invite_code": invite_code})

    res_3 = auth_client.get(f"/api/ecosystem/educator/cohorts/{cohort_id}/analytics")
    assert res_3.json()["privacy_status"] == "LIMITED_SUMMARY"

def test_team_project_sharing_isolation(auth_client, client, db_session, test_user):
    clean_state(db_session, test_user.id)

    # User A project (to share) and User A private project (not shared)
    p_shared = Project(user_id=test_user.id, github_repo_id=random.randint(100000, 999999), name="TeamSharedMicroservice", is_public=False)
    p_private = Project(user_id=test_user.id, github_repo_id=random.randint(100000, 999999), name="UserA_SecretPersonalApp", is_public=False)
    db_session.add_all([p_shared, p_private])
    db_session.commit()

    # User A creates team
    res_team = auth_client.post(
        "/api/ecosystem/teams",
        json={"name": "Alpha Engineering", "description": "Backend Team"}
    )
    assert res_team.status_code == 201
    team_id = res_team.json()["team_id"]

    # User A shares only p_shared
    res_share = auth_client.post(
        f"/api/ecosystem/teams/{team_id}/share-project",
        json={"project_id": p_shared.id}
    )
    assert res_share.status_code == 200

    # User B joins team
    user_b = User(email="member_b@test.com", password_hash="hash")
    db_session.add(user_b)
    db_session.commit()
    token_b = create_access_token(user_b.id)

    t_rec = db_session.query(Team).filter(Team.id == team_id).first()
    client_b = TestClient(app)
    client_b.cookies.set("access_token", token_b)
    client_b.post("/api/ecosystem/teams/join", json={"invite_code": t_rec.invite_code})

    # User B checks team collaboration map
    res_collab = client_b.get(f"/api/ecosystem/teams/{team_id}/collaboration")
    assert res_collab.status_code == 200
    collab = res_collab.json()

    shared_names = [p["name"] for p in collab["shared_projects"]]
    assert "TeamSharedMicroservice" in shared_names
    assert "UserA_SecretPersonalApp" not in shared_names  # Personal repo never leaked!

def test_sharing_center_control_plane(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    res = auth_client.get("/api/ecosystem/sharing")
    assert res.status_code == 200
    data = res.json()
    assert "permissions_ledger" in data
    assert "active_mentors_count" in data
    assert "active_review_links_count" in data
