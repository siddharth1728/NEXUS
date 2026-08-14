import pytest
from app.models.user import User, Gap, UserSkill, SkillState
from app.models.taxonomy import Skill
from app.models.project import (
    Project, RepositorySnapshot, Artifact, RawObservation,
    Evidence, EvidenceType, EvidenceSkill, SnapshotStatus
)
from app.services.project_intelligence_service import get_project_intelligence

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

def test_unauthenticated_intelligence_rejected(client):
    resp = client.get("/api/projects/1/intelligence")
    assert resp.status_code == 401

def test_cross_user_intelligence_isolation(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    # Other user and project
    other_user = User(email="other_proj_intel@example.com", password_hash="hash")
    db_session.add(other_user)
    db_session.commit()

    other_project = Project(user_id=other_user.id, github_repo_id=888, name="PrivateProject")
    db_session.add(other_project)
    db_session.commit()

    # Attempting to access other user's project intelligence must return 404
    resp = auth_client.get(f"/api/projects/{other_project.id}/intelligence")
    assert resp.status_code == 404

def test_empty_project_intelligence(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    p = Project(user_id=test_user.id, github_repo_id=501, name="FreshRepo")
    db_session.add(p)
    db_session.commit()

    resp = auth_client.get(f"/api/projects/{p.id}/intelligence")
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["metadata"]["name"] == "FreshRepo"
    assert data["metadata"]["artifact_count"] == 0
    assert data["depth_level"] == "UNSURVEYED"
    assert data["guidance"]["recommendation"] == "SURVEY_REQUIRED"
    assert data["evidence_categories"] == []
    assert data["evolution"] == []

def test_project_intelligence_with_evidence_and_signals(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)

    s_api = get_or_create_skill(db_session, "REST APIs")
    s_db = get_or_create_skill(db_session, "PostgreSQL")
    s_testing = get_or_create_skill(db_session, "Testing")
    s_python = get_or_create_skill(db_session, "Python")

    # User skills (Python is prerequisite for Testing quest)
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_python.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_api.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_db.id, state=SkillState.DEVELOPING, calculation_version="v1"))
    db_session.add(Gap(user_id=test_user.id, skill_id=s_testing.id, actual_state=SkillState.MISSING, required_state=SkillState.STRONG, state_distance=3, importance_weight=1.0, severity=3.0, calculation_version="v1"))

    # Project and snapshot
    p = Project(user_id=test_user.id, github_repo_id=502, name="EcommerceBackend")
    db_session.add(p)
    db_session.commit()

    snap = RepositorySnapshot(
        project_id=p.id,
        commit_sha="abcdef123456",
        branch="main",
        status=SnapshotStatus.COMPLETED
    )
    db_session.add(snap)
    db_session.commit()

    # Artifacts & Observations
    a1 = Artifact(snapshot_id=snap.id, file_path="app/routers/items.py", type="PYTHON_FILE")
    a2 = Artifact(snapshot_id=snap.id, file_path="app/database.py", type="PYTHON_FILE")
    db_session.add_all([a1, a2])
    db_session.commit()

    obs1 = RawObservation(artifact_id=a1.id, observation_text="FastAPI route handlers detected")
    obs2 = RawObservation(artifact_id=a2.id, observation_text="PostgreSQL configuration detected")
    db_session.add_all([obs1, obs2])
    db_session.commit()

    # Evidence
    ev1 = Evidence(raw_observation_id=obs1.id, type=EvidenceType.API, quality_score=0.85, freshness_weight=1.0, source_reference="app/routers/items.py")
    ev2 = Evidence(raw_observation_id=obs2.id, type=EvidenceType.DATABASE, quality_score=0.75, freshness_weight=1.0, source_reference="app/database.py")
    db_session.add_all([ev1, ev2])
    db_session.commit()

    db_session.add(EvidenceSkill(evidence_id=ev1.id, skill_id=s_api.id))
    db_session.add(EvidenceSkill(evidence_id=ev2.id, skill_id=s_db.id))
    db_session.commit()

    resp = auth_client.get(f"/api/projects/{p.id}/intelligence")
    assert resp.status_code == 200
    data = resp.json()

    # 1. Metadata check
    assert data["metadata"]["name"] == "EcommerceBackend"
    assert "Python" in data["metadata"]["detected_languages"]
    assert "FastAPI" in data["metadata"]["detected_frameworks"]
    assert "PostgreSQL" in data["metadata"]["detected_frameworks"]

    # 2. Depth check
    assert data["depth_level"] in ["EXPANDING", "BROAD_SIGNAL", "FOUNDATION"]

    # 3. Signals check (REST APIs is STRONG, PostgreSQL is DEVELOPING, Testing is UNEXPLORED)
    signals_by_name = {s["skill_name"]: s for s in data["signals"]}
    assert "REST APIs" in signals_by_name
    assert signals_by_name["REST APIs"]["state"] == "STRONG"
    assert "PostgreSQL" in signals_by_name
    assert signals_by_name["PostgreSQL"]["state"] == "DEVELOPING"
    assert "Testing" in signals_by_name
    assert signals_by_name["Testing"]["state"] == "UNEXPLORED"

    # 4. Dimension Coverage check
    dim_by_name = {d["dimension_name"]: d for d in data["dimensions"]}
    assert dim_by_name["CORE_API"]["status"] == "PROVEN"
    assert dim_by_name["DATABASE"]["status"] == "DEVELOPING"
    assert dim_by_name["TESTING"]["status"] == "NOT_OBSERVED"

    # 5. Strategic Guidance check
    assert data["guidance"]["recommendation"] == "IMPROVE_THIS_PROJECT"
    assert "Testing" in data["guidance"]["missing_dimensions"] or "Automated Testing" in data["guidance"]["missing_dimensions"]

    # 6. Growth Opportunities (Proof Quest for testing)
    growth_actions = [g["action_key"] for g in data["growth_opportunities"]]
    assert "ADD_API_TESTS" in growth_actions

    # 7. Evolution History check
    assert len(data["evolution"]) == 1
    assert data["evolution"][0]["survey_number"] == 1
    assert "API" in data["evolution"][0]["new_evidence_types"]
    assert "DATABASE" in data["evolution"][0]["new_evidence_types"]

def test_truth_contract_no_fake_scores(auth_client, db_session, test_user):
    """Ensure project intelligence response exposes only factual signals, no fake % scores."""
    clean_state(db_session, test_user.id)

    p = Project(user_id=test_user.id, github_repo_id=503, name="TruthProject")
    db_session.add(p)
    db_session.commit()

    resp = auth_client.get(f"/api/projects/{p.id}/intelligence")
    assert resp.status_code == 200
    data = resp.json()

    # Verify no arbitrary numerical rating fields exist
    assert "project_score" not in data
    assert "overall_percentage" not in data
    assert "industry_ready" not in data
