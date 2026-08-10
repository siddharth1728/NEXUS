import pytest
from datetime import datetime, timezone, timedelta
from app.services.evidence_engine import _match_rule, calculate_freshness, rebuild_snapshot_evidence
from app.models.project import EvidenceType, RawObservation, Artifact, RepositorySnapshot, Evidence, EvidenceSkill, Project, SnapshotStatus
from app.models.taxonomy import Skill

def test_evidence_classification():
    # 1. FastAPI import
    rule = _match_rule("fastapi import detected")
    assert rule is not None
    assert rule["type"] == EvidenceType.API
    assert rule["quality_score"] == 0.8
    assert "REST APIs" in rule["target_skills"]
    
    # 2. Pytest function
    rule = _match_rule("pytest test function detected in main.py")
    assert rule is not None
    assert rule["type"] == EvidenceType.TESTING
    assert rule["quality_score"] == 0.9
    
    # 3. Vanity metrics
    rule = _match_rule("github repository has 50 stars")
    assert rule is None
    
    rule = _match_rule("repository popularity is high")
    assert rule is None

def test_freshness_calculation():
    now = datetime.now(timezone.utc)
    
    # Current
    assert calculate_freshness(now) == 1.0
    
    # Half year old (182.5 days -> ~0.5)
    half_year = now - timedelta(days=182)
    freshness = calculate_freshness(half_year)
    assert 0.49 < freshness < 0.51
    
    # Over a year old (should floor at 0.1)
    two_years = now - timedelta(days=730)
    assert calculate_freshness(two_years) == 0.1

def test_engine_rebuildability(db_session, test_user):
    skill1 = db_session.query(Skill).filter(Skill.name == "REST APIs").first()
    if not skill1:
        skill1 = Skill(name="REST APIs", category="API")
        db_session.add(skill1)
        db_session.commit()
    
    skill2 = db_session.query(Skill).filter(Skill.name == "Python").first()
    if not skill2:
        skill2 = Skill(name="Python", category="API")
        db_session.add(skill2)
        db_session.commit()

    # Create project and snapshot
    project = Project(user_id=test_user.id, github_repo_id=123, name="test-repo")
    db_session.add(project)
    db_session.commit()
    
    snapshot = RepositorySnapshot(project_id=project.id, status=SnapshotStatus.COMPLETED)
    db_session.add(snapshot)
    db_session.commit()
    
    artifact = Artifact(snapshot_id=snapshot.id, file_path="main.py", type="blob")
    db_session.add(artifact)
    db_session.commit()
    
    obs = RawObservation(artifact_id=artifact.id, observation_text="fastapi import detected")
    db_session.add(obs)
    db_session.commit()
    
    # Run rebuild
    rebuild_snapshot_evidence(snapshot.id, db_session)
    
    # Check evidence
    evidence = db_session.query(Evidence).filter(Evidence.raw_observation_id == obs.id).first()
    assert evidence is not None
    assert evidence.type == EvidenceType.API
    assert evidence.quality_score == 0.8
    assert evidence.source_reference == "main.py"
    
    skills = [s.skill.name for s in evidence.skills]
    assert "REST APIs" in skills
    assert "Python" in skills
    
    # Test idempotency / rebuild
    rebuild_snapshot_evidence(snapshot.id, db_session)
    evidence_count = db_session.query(Evidence).filter(Evidence.raw_observation_id == obs.id).count()
    assert evidence_count == 1 # Only one evidence record per observation

def test_unknown_skills_ignored(db_session, test_user):
    # Setup ONLY one skill, but the rule requires two ("REST APIs", "Python")
    # Delete Python skill if it exists from previous tests
    python_skill = db_session.query(Skill).filter(Skill.name == "Python").first()
    if python_skill:
        db_session.delete(python_skill)
        db_session.commit()

    skill1 = db_session.query(Skill).filter(Skill.name == "REST APIs").first()
    if not skill1:
        skill1 = Skill(name="REST APIs", category="API")
        db_session.add(skill1)
        db_session.commit()

    project = Project(user_id=test_user.id, github_repo_id=124, name="test-repo-2")
    db_session.add(project)
    db_session.commit()
    
    snapshot = RepositorySnapshot(project_id=project.id, status=SnapshotStatus.COMPLETED)
    db_session.add(snapshot)
    db_session.commit()
    
    artifact = Artifact(snapshot_id=snapshot.id, file_path="main.py", type="blob")
    db_session.add(artifact)
    db_session.commit()
    
    obs = RawObservation(artifact_id=artifact.id, observation_text="fastapi import detected")
    db_session.add(obs)
    db_session.commit()
    
    rebuild_snapshot_evidence(snapshot.id, db_session)
    
    evidence = db_session.query(Evidence).filter(Evidence.raw_observation_id == obs.id).first()
    assert len(evidence.skills) == 1
    assert evidence.skills[0].skill.name == "REST APIs"
    # "Python" was safely ignored because it wasn't in the DB.
