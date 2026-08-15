import pytest
from app.models.user import User, UserSkill, Gap, SkillState
from app.models.profile import StudentProfile
from app.models.taxonomy import TargetRole, Skill, TargetRoleSkill
from app.models.project import Project, RepositorySnapshot, Artifact, RawObservation, Evidence, EvidenceType, EvidenceSkill, SnapshotStatus
from app.models.claims import UserClaim
from app.core.security import create_access_token

def clean_state(db, user_id):
    db.query(UserClaim).filter(UserClaim.user_id == user_id).delete(synchronize_session=False)
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

def test_public_profile_unavailable_when_private(client, db_session, test_user):
    clean_state(db_session, test_user.id)

    profile = db_session.query(StudentProfile).filter(StudentProfile.user_id == test_user.id).first()
    if not profile:
        profile = StudentProfile(user_id=test_user.id, name="Test User", public_slug="test_slug_priv", public_profile=False)
        db_session.add(profile)
    else:
        profile.public_slug = "test_slug_priv"
        profile.public_profile = False
    db_session.commit()

    # Anonymous visitor accessing private profile
    res = client.get(f"/api/public-profiles/test_slug_priv")
    assert res.status_code == 404

    # Public atlas endpoint also unavailable
    res_atlas = client.get(f"/api/public-profiles/test_slug_priv/atlas")
    assert res_atlas.status_code == 404

def test_public_profile_active_and_data_sanitization(client, auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    s_python = db_session.query(Skill).filter(Skill.name == "Python").first()
    if not s_python:
        s_python = Skill(name="Python", category="Language", description="Python programming")
        db_session.add(s_python)
        db_session.commit()

    s_docker = db_session.query(Skill).filter(Skill.name == "Docker").first()
    if not s_docker:
        s_docker = Skill(name="Docker", category="DevOps", description="Docker containers")
        db_session.add(s_docker)
        db_session.commit()

    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_python.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_docker.id, state=SkillState.DEVELOPING, calculation_version="v1"))
    db_session.commit()

    # Create 2 projects: 1 public, 1 private
    p_pub = Project(user_id=test_user.id, github_repo_id=101, name="PublicNexusService", is_public=True)
    p_priv = Project(user_id=test_user.id, github_repo_id=102, name="SecretInternalRepo", is_public=False)
    db_session.add_all([p_pub, p_priv])
    db_session.commit()

    # Snapshot and evidence for public project
    snap = RepositorySnapshot(project_id=p_pub.id, commit_sha="pub123", branch="main", status=SnapshotStatus.COMPLETED)
    db_session.add(snap)
    db_session.commit()

    art = Artifact(snapshot_id=snap.id, file_path="app/main.py", type="PYTHON_FILE")
    db_session.add(art)
    db_session.commit()

    obs = RawObservation(artifact_id=art.id, observation_text="FastAPI endpoints and routers defined")
    db_session.add(obs)
    db_session.commit()

    ev = Evidence(raw_observation_id=obs.id, type=EvidenceType.API, quality_score=0.9, freshness_weight=1.0, source_reference="app/main.py")
    db_session.add(ev)
    db_session.commit()

    db_session.add(EvidenceSkill(evidence_id=ev.id, skill_id=s_python.id))
    db_session.commit()

    # Enable public profile with email hidden
    res_update = auth_client.put(
        "/api/profile/nexus-id",
        json={
            "public_profile": True,
            "public_slug": "nx_test_active",
            "bio": "Senior backend engineer focused on verifiable systems.",
            "show_email": False,
            "show_proof": True,
            "show_journey": True,
            "publish_project_ids": [p_pub.id],
            "featured_project_ids": [p_pub.id]
        }
    )
    assert res_update.status_code == 200

    # Anonymous visitor retrieves public profile
    res_pub = client.get("/api/public-profiles/nx_test_active")
    assert res_pub.status_code == 200
    data = res_pub.json()

    assert data["public_slug"] == "nx_test_active"
    assert data["nexus_id"].startswith("NX-")
    assert "Python" in data["proven_signals"]
    assert "Docker" in data["developing_signals"]
    assert data["contact_email"] is None  # Sanitized: email hidden
    
    # Verify ONLY public projects appear
    proj_names = [p["name"] for p in data["featured_projects"]]
    assert "PublicNexusService" in proj_names
    assert "SecretInternalRepo" not in proj_names  # Private repo never leaked!

def test_slug_customization_and_uniqueness(auth_client, client, db_session, test_user):
    clean_state(db_session, test_user.id)

    # 1. Update to valid slug
    res = auth_client.put(
        "/api/profile/nexus-id",
        json={"public_slug": "alex_architect"}
    )
    assert res.status_code == 200
    assert res.json()["public_slug"] == "alex_architect"

    # 2. Invalid slug rejected (spaces or special characters)
    res_inv = auth_client.put(
        "/api/profile/nexus-id",
        json={"public_slug": "invalid slug with spaces!"}
    )
    assert res_inv.status_code == 400

    # 3. Create User B and attempt to take User A's slug
    user_b = User(email="user_b@nexus.test", password_hash="hash")
    db_session.add(user_b)
    db_session.commit()
    token_b = create_access_token(user_b.id)

    from fastapi.testclient import TestClient
    from app.main import app
    client_b = TestClient(app)
    client_b.cookies.set("access_token", token_b)

    res_taken = client_b.put(
        "/api/profile/nexus-id",
        json={"public_slug": "alex_architect"}
    )
    assert res_taken.status_code == 400
    assert "already taken" in res_taken.json()["detail"]

def test_featured_project_strict_ownership(auth_client, client, db_session, test_user):
    clean_state(db_session, test_user.id)

    p_a = Project(user_id=test_user.id, github_repo_id=201, name="UserA_Project", is_public=True)
    db_session.add(p_a)
    db_session.commit()

    # User B
    user_b = User(email="intruder@nexus.test", password_hash="hash")
    db_session.add(user_b)
    db_session.commit()
    p_b = Project(user_id=user_b.id, github_repo_id=202, name="UserB_Project", is_public=True)
    db_session.add(p_b)
    db_session.commit()

    # User A tries to feature User B's project (IDOR attempt)
    res = auth_client.put(
        "/api/profile/nexus-id",
        json={"featured_project_ids": [p_b.id, p_a.id]}
    )
    assert res.status_code == 200
    data = res.json()
    # Server-side validation MUST strip out p_b.id and only keep p_a.id
    assert p_b.id not in data["featured_project_ids"]
    assert p_a.id in data["featured_project_ids"]

def test_claim_vs_proof_three_state_evaluation(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    s_sql = db_session.query(Skill).filter(Skill.name == "PostgreSQL").first()
    if not s_sql:
        s_sql = Skill(name="PostgreSQL", category="Database", description="PostgreSQL DB")
        db_session.add(s_sql)
        db_session.commit()

    s_test = db_session.query(Skill).filter(Skill.name == "Testing").first()
    if not s_test:
        s_test = Skill(name="Testing", category="Quality", description="Automated testing")
        db_session.add(s_test)
        db_session.commit()

    # PostgreSQL is STRONG, Testing is DEVELOPING, Kubernetes is MISSING/UNEXPLORED
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_sql.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_test.id, state=SkillState.DEVELOPING, calculation_version="v1"))
    db_session.commit()

    # Register 3 claims
    auth_client.post("/api/career/claims", json={"claim_text": "PostgreSQL"})
    auth_client.post("/api/career/claims", json={"claim_text": "Testing"})
    auth_client.post("/api/career/claims", json={"claim_text": "Kubernetes"})

    res = auth_client.get("/api/career/claims")
    assert res.status_code == 200
    claims = res.json()["claims"]
    assert len(claims) == 3

    claim_map = {c["claim_text"]: c["status"] for c in claims}
    assert claim_map["PostgreSQL"] == "SUPPORTED"
    assert claim_map["Testing"] == "PARTIALLY_SUPPORTED"
    assert claim_map["Kubernetes"] == "NOT_YET_SUPPORTED"

def test_portfolio_selector_deterministic_reasoning(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    role = db_session.query(TargetRole).filter(TargetRole.name == "Backend Engineer").first()
    if not role:
        role = TargetRole(name="Backend Engineer", description="Backend Systems")
        db_session.add(role)
        db_session.commit()

    s_api = db_session.query(Skill).filter(Skill.name == "REST APIs").first()
    if not s_api:
        s_api = Skill(name="REST APIs", category="API", description="API design")
        db_session.add(s_api)
        db_session.commit()

    db_session.add(TargetRoleSkill(target_role_id=role.id, skill_id=s_api.id, minimum_expected_state="STRONG"))
    
    profile = db_session.query(StudentProfile).filter(StudentProfile.user_id == test_user.id).first()
    if profile:
        profile.target_role_id = role.id
    else:
        profile = StudentProfile(user_id=test_user.id, target_role_id=role.id)
        db_session.add(profile)
    db_session.commit()

    # Create project with REST API evidence
    p = Project(user_id=test_user.id, github_repo_id=501, name="PaymentGatewayService", is_public=True)
    db_session.add(p)
    db_session.commit()

    snap = RepositorySnapshot(project_id=p.id, commit_sha="501sha", branch="main", status=SnapshotStatus.COMPLETED)
    db_session.add(snap)
    db_session.commit()

    art = Artifact(snapshot_id=snap.id, file_path="app/routes.py", type="PYTHON_FILE")
    db_session.add(art)
    db_session.commit()

    obs = RawObservation(artifact_id=art.id, observation_text="REST endpoints for billing")
    db_session.add(obs)
    db_session.commit()

    ev = Evidence(raw_observation_id=obs.id, type=EvidenceType.API, quality_score=0.9, freshness_weight=1.0, source_reference="app/routes.py")
    db_session.add(ev)
    db_session.commit()

    db_session.add(EvidenceSkill(evidence_id=ev.id, skill_id=s_api.id))
    db_session.commit()

    # Query Portfolio Selector
    res = auth_client.get("/api/career/portfolio-selector")
    assert res.status_code == 200
    data = res.json()
    assert data["recommended_project_name"] == "PaymentGatewayService"
    assert any("REST APIs" in r for r in data["reasoning"])

def test_public_atlas_projection(client, auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    p = Project(user_id=test_user.id, github_repo_id=601, name="PublicAtlasApp", is_public=True)
    db_session.add(p)
    db_session.commit()

    auth_client.put(
        "/api/profile/nexus-id",
        json={
            "public_profile": True,
            "public_slug": "atlas_pilot",
            "publish_project_ids": [p.id]
        }
    )

    res = client.get("/api/public-profiles/atlas_pilot/atlas")
    assert res.status_code == 200
    atlas = res.json()
    assert atlas["nexus_id"].startswith("NX-")
    assert "territories" in atlas
