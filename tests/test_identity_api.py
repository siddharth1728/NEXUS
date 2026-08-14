import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, UserSkill, SkillState, UserSkillHistory
from app.models.taxonomy import Skill
from app.models.project import Project, RepositorySnapshot, Artifact, RawObservation, Evidence, EvidenceType, EvidenceSkill
from datetime import datetime, timezone

client = TestClient(app)

def test_get_identity_unauthenticated():
    response = client.get("/api/identity")
    assert response.status_code == 401

def test_get_identity_authenticated(db_session, test_user, auth_client):
    # Setup skills
    import uuid
    uid = uuid.uuid4().hex[:8]
    skill1 = Skill(name=f"Skill1_{uid}", category="TestCategory")
    skill2 = Skill(name=f"Skill2_{uid}", category="TestCategory")
    db_session.add(skill1)
    db_session.add(skill2)
    db_session.commit()
    
    us1 = UserSkill(user_id=test_user.id, skill_id=skill1.id, state=SkillState.STRONG, calculation_version="v1")
    us2 = UserSkill(user_id=test_user.id, skill_id=skill2.id, state=SkillState.MISSING, calculation_version="v1")
    db_session.add(us1)
    db_session.add(us2)
    db_session.commit()
    
    # Setup project and snapshot
    import random
    repo_id = random.randint(1000, 9000000)
    project = Project(user_id=test_user.id, github_repo_id=repo_id, name=f"TestRepo_{uid}")
    db_session.add(project)
    db_session.commit()
    
    snap = RepositorySnapshot(project_id=project.id, captured_at=datetime.now(timezone.utc))
    db_session.add(snap)
    db_session.commit()
    
    # Setup Artifact, RawObs, Evidence for Skill1
    art = Artifact(snapshot_id=snap.id, file_path="main.py", type="CODE")
    db_session.add(art)
    db_session.commit()
    
    ro = RawObservation(artifact_id=art.id, observation_text="Observed something")
    db_session.add(ro)
    db_session.commit()
    
    ev = Evidence(raw_observation_id=ro.id, type=EvidenceType.IMPLEMENTATION, quality_score=1.0, freshness_weight=1.0)
    db_session.add(ev)
    db_session.commit()
    
    es = EvidenceSkill(evidence_id=ev.id, skill_id=skill1.id)
    db_session.add(es)
    db_session.commit()
    
    # Setup history transition
    history = UserSkillHistory(user_id=test_user.id, skill_id=skill2.id, previous_state=SkillState.WEAK.value, new_state=SkillState.MISSING.value, snapshot_id=snap.id)
    db_session.add(history)
    db_session.commit()
    
    # Call API
    response = auth_client.get("/api/identity")
    assert response.status_code == 200
    data = response.json()
    
    # Assert Atlas Territories
    # Find the specific category we created, filtering out any from other tests
    territory = next((t for t in data["atlas_territories"] if t["category"] == "TestCategory"), None)
    assert territory is not None
    
    # Landmark and signal
    landmark = next((l for l in territory["landmarks"] if l["project_name"] == f"TestRepo_{uid}"), None)
    assert landmark is not None
    assert landmark["signals"][0]["skill_name"] == f"Skill1_{uid}"
    assert landmark["signals"][0]["evidence"][0]["observation"] == "Observed something"
    
    # Unexplored
    unexplored = next((u for u in territory["unexplored"] if u["skill_name"] == f"Skill2_{uid}"), None)
    assert unexplored is not None
    
    # Journey
    journey = data["engineering_journey"]
    transition = next((t for t in journey["meaningful_transitions"] if t["skill_name"] == f"Skill2_{uid}"), None)
    assert transition is not None
    
    discovery = next((d for d in journey["recent_discoveries"] if d["observation"] == "Observed something"), None)
    assert discovery is not None

def test_identity_user_isolation(db_session, test_user, auth_client):
    import uuid
    user2 = User(email=f"user2_{uuid.uuid4()}@example.com", password_hash="pw")
    db_session.add(user2)
    db_session.commit()
    
    skill = Skill(name="IsoSkill", category="IsoCategory")
    db_session.add(skill)
    db_session.commit()
    
    us2 = UserSkill(user_id=user2.id, skill_id=skill.id, state=SkillState.MISSING, calculation_version="v1")
    db_session.add(us2)
    db_session.commit()
    
    response = auth_client.get("/api/identity")
    assert response.status_code == 200
    data = response.json()
    
    # Should not see user2's category
    assert not any(t["category"] == "IsoCategory" for t in data["atlas_territories"])
