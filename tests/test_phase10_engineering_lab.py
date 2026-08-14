import pytest
from app.models.user import User, UserSkill, Gap, SkillState
from app.models.taxonomy import Skill
from app.models.project import (
    Project, RepositorySnapshot, Artifact, RawObservation,
    Evidence, EvidenceType, EvidenceSkill, SnapshotStatus
)
from app.config.concept_catalog import get_concept_catalog

def get_or_create_skill(db, name, category="Backend"):
    s = db.query(Skill).filter(Skill.name == name).first()
    if not s:
        s = Skill(name=name, category=category)
        db.add(s)
        db.commit()
    return s

def clean_state(db_session, user_id):
    db_session.query(Project).filter(Project.user_id == user_id).delete()
    db_session.query(Gap).filter(Gap.user_id == user_id).delete()
    db_session.query(UserSkill).filter(UserSkill.user_id == user_id).delete()
    db_session.commit()

def test_unauthenticated_lab_access_rejected(client):
    resp = client.get("/api/lab/concepts")
    assert resp.status_code == 401

    resp = client.get("/api/lab/discovery")
    assert resp.status_code == 401

def test_concept_catalog_loads_deterministically(auth_client):
    resp = auth_client.get("/api/lab/concepts")
    assert resp.status_code == 200
    concepts = resp.json()
    assert len(concepts) >= 7

    keys = [c["concept_key"] for c in concepts]
    assert "HTTP_REQUEST_LIFECYCLE" in keys
    assert "AUTHENTICATION_FLOWS" in keys
    assert "AUTOMATED_TESTING" in keys
    assert "CONTAINERIZATION_DOCKER" in keys
    assert "DATABASE_PERSISTENCE" in keys

def test_concept_detail_with_project_evidence(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    s_testing = get_or_create_skill(db_session, "Testing")
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_testing.id, state=SkillState.DEVELOPING, calculation_version="v1"))

    # Create project with testing evidence
    p = Project(user_id=test_user.id, github_repo_id=701, name="PaymentService")
    db_session.add(p)
    db_session.commit()

    snap = RepositorySnapshot(project_id=p.id, commit_sha="testsha123", branch="main", status=SnapshotStatus.COMPLETED)
    db_session.add(snap)
    db_session.commit()

    art = Artifact(snapshot_id=snap.id, file_path="tests/test_payments.py", type="PYTHON_FILE")
    db_session.add(art)
    db_session.commit()

    obs = RawObservation(artifact_id=art.id, observation_text="Pytest assertion test functions detected")
    db_session.add(obs)
    db_session.commit()

    ev = Evidence(raw_observation_id=obs.id, type=EvidenceType.TESTING, quality_score=0.9, freshness_weight=1.0, source_reference="tests/test_payments.py")
    db_session.add(ev)
    db_session.commit()

    db_session.add(EvidenceSkill(evidence_id=ev.id, skill_id=s_testing.id))
    db_session.commit()

    # Query concept detail for AUTOMATED_TESTING
    resp = auth_client.get("/api/lab/concepts/AUTOMATED_TESTING")
    assert resp.status_code == 200
    data = resp.json()

    assert data["concept_key"] == "AUTOMATED_TESTING"
    assert "PaymentService" in data["why_user_is_seeing_this"]
    assert len(data["user_projects_using_this"]) == 1
    assert data["user_projects_using_this"][0]["project_name"] == "PaymentService"
    assert "tests/test_payments.py" in data["user_projects_using_this"][0]["sample_source_files"]

    # Verify 2D Diagram and Try-It challenge
    assert len(data["diagram_steps"]) >= 4
    assert data["try_it_challenge"]["prompt"] != ""
    assert len(data["try_it_challenge"]["options"]) >= 2

def test_concept_detail_unknown_404(auth_client):
    resp = auth_client.get("/api/lab/concepts/NON_EXISTENT_CONCEPT")
    assert resp.status_code == 404

def test_lab_discovery_feed(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    # Gap for Docker
    s_docker = get_or_create_skill(db_session, "Docker")
    db_session.add(Gap(user_id=test_user.id, skill_id=s_docker.id, actual_state=SkillState.MISSING, required_state=SkillState.STRONG, state_distance=3, importance_weight=1.0, severity=3.0, calculation_version="v1"))
    db_session.commit()

    resp = auth_client.get("/api/lab/discovery")
    assert resp.status_code == 200
    data = resp.json()

    assert "featured_discovery" in data
    assert "discovery_reason" in data
    assert len(data["all_concepts"]) >= 7

def test_cross_user_lab_isolation(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    # Other user with Auth project
    other_user = User(email="other_lab_user@example.com", password_hash="hash")
    db_session.add(other_user)
    db_session.commit()

    p_other = Project(user_id=other_user.id, github_repo_id=702, name="SecretAuthRepo")
    db_session.add(p_other)
    db_session.commit()

    snap = RepositorySnapshot(project_id=p_other.id, status=SnapshotStatus.COMPLETED)
    db_session.add(snap)
    db_session.commit()

    art = Artifact(snapshot_id=snap.id, file_path="app/auth.py", type="PYTHON_FILE")
    db_session.add(art)
    db_session.commit()

    obs = RawObservation(artifact_id=art.id, observation_text="JWT signature routines")
    db_session.add(obs)
    db_session.commit()

    ev = Evidence(raw_observation_id=obs.id, type=EvidenceType.AUTHENTICATION, quality_score=0.9, freshness_weight=1.0)
    db_session.add(ev)
    db_session.commit()

    # When test_user views AUTHENTICATION_FLOWS, other user's SecretAuthRepo must NOT appear!
    resp = auth_client.get("/api/lab/concepts/AUTHENTICATION_FLOWS")
    assert resp.status_code == 200
    data = resp.json()

    project_names = [p["project_name"] for p in data["user_projects_using_this"]]
    assert "SecretAuthRepo" not in project_names

def test_critical_truth_contract_learning_does_not_mutate_skill_or_gap(auth_client, db_session, test_user):
    """
    CRITICAL TRUTH CONTRACT:
    Opening Engineering Lab, reading concepts, or answering challenges MUST NOT:
    1. Change UserSkill state
    2. Change Gap state
    3. Create Evidence or RawObservation
    """
    clean_state(db_session, test_user.id)

    s_testing = get_or_create_skill(db_session, "Testing")
    gap = Gap(user_id=test_user.id, skill_id=s_testing.id, actual_state=SkillState.MISSING, required_state=SkillState.STRONG, state_distance=3, importance_weight=1.0, severity=3.0, calculation_version="v1")
    db_session.add(gap)
    db_session.commit()

    # User accesses lab and concept
    resp = auth_client.get("/api/lab/discovery")
    assert resp.status_code == 200
    resp = auth_client.get("/api/lab/concepts/AUTOMATED_TESTING")
    assert resp.status_code == 200

    # Verify database: Gap must remain MISSING, UserSkill must NOT exist, Evidence count must be 0
    db_gap = db_session.query(Gap).filter(Gap.user_id == test_user.id, Gap.skill_id == s_testing.id).first()
    assert db_gap is not None
    assert db_gap.actual_state == SkillState.MISSING

    user_skill = db_session.query(UserSkill).filter(UserSkill.user_id == test_user.id, UserSkill.skill_id == s_testing.id).first()
    assert user_skill is None
