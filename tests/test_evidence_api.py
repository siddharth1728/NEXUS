import pytest
from app.models.project import Project, RepositorySnapshot, Artifact, RawObservation, Evidence, EvidenceSkill, EvidenceType, SnapshotStatus
from app.models.taxonomy import Skill

def test_get_evidence_by_snapshot(auth_client, db_session, test_user):
    # Setup data
    project = Project(user_id=test_user.id, github_repo_id=999, name="api-test-repo")
    db_session.add(project)
    db_session.commit()
    
    snapshot = RepositorySnapshot(project_id=project.id, status=SnapshotStatus.COMPLETED)
    db_session.add(snapshot)
    db_session.commit()
    
    artifact = Artifact(snapshot_id=snapshot.id, file_path="main.py", type="blob")
    db_session.add(artifact)
    db_session.commit()
    
    obs = RawObservation(artifact_id=artifact.id, observation_text="jwt authentication implementation detected")
    db_session.add(obs)
    db_session.commit()
    
    # Let's bypass engine and create Evidence directly for testing API
    evidence = Evidence(raw_observation_id=obs.id, type=EvidenceType.AUTHENTICATION, quality_score=0.9, freshness_weight=1.0, source_reference="main.py")
    db_session.add(evidence)
    db_session.commit()
    
    response = auth_client.get(f"/api/snapshots/{snapshot.id}/evidence")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == EvidenceType.AUTHENTICATION
    assert data[0]["source_reference"] == "main.py"

def test_cross_user_evidence_access(auth_client, db_session, test_user):
    # Create another user and their project
    from app.models.user import User
    import uuid
    other_user = User(email=f"other_{uuid.uuid4()}@example.com", password_hash="pw")
    db_session.add(other_user)
    db_session.commit()
    
    project = Project(user_id=other_user.id, github_repo_id=888, name="other-repo")
    db_session.add(project)
    db_session.commit()
    
    snapshot = RepositorySnapshot(project_id=project.id, status=SnapshotStatus.COMPLETED)
    db_session.add(snapshot)
    db_session.commit()
    
    # 1. Attempt to fetch evidence by snapshot ID
    res = auth_client.get(f"/api/snapshots/{snapshot.id}/evidence")
    assert res.status_code == 404
    
    # Add evidence
    artifact = Artifact(snapshot_id=snapshot.id, file_path="main.py", type="blob")
    db_session.add(artifact)
    db_session.commit()
    
    obs = RawObservation(artifact_id=artifact.id, observation_text="fastapi import detected")
    db_session.add(obs)
    db_session.commit()
    
    evidence = Evidence(raw_observation_id=obs.id, type=EvidenceType.API, quality_score=0.8, freshness_weight=1.0)
    db_session.add(evidence)
    db_session.commit()
    
    # 2. Attempt to fetch evidence by ID
    res = auth_client.get(f"/api/evidence/{evidence.id}")
    assert res.status_code == 404
    
    # 3. Attempt to fetch evidence skills
    res = auth_client.get(f"/api/evidence/{evidence.id}/skills")
    assert res.status_code == 404
    
def test_skill_evidence_isolation(auth_client, db_session, test_user):
    skill = db_session.query(Skill).filter(Skill.name == "Python").first()
    if not skill:
        skill = Skill(name="Python", category="API")
        db_session.add(skill)
        db_session.commit()
    
    res = auth_client.get(f"/api/skills/{skill.id}/evidence")
    assert res.status_code == 200
    assert len(res.json()) == 0
