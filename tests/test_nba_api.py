import pytest
from app.models.user import User, Gap, UserSkill, SkillState
from app.models.taxonomy import Skill
from app.models.project import Project
from app.models.action import Recommendation, ActionHistory, ActionHistoryStatus

def get_or_create_skill(db, name, category="Cat"):
    s = db.query(Skill).filter(Skill.name == name).first()
    if not s:
        s = Skill(name=name, category=category)
        db.add(s)
        db.commit()
    return s

def test_unauthenticated_nba_access_rejected(client):
    response = client.get("/api/next-best-action")
    assert response.status_code == 401

def test_get_nba(auth_client, db_session, test_user):
    # Setup state so there's an NBA
    db_session.query(ActionHistory).filter(ActionHistory.user_id == test_user.id).delete()
    db_session.query(Recommendation).filter(Recommendation.user_id == test_user.id).delete()
    db_session.query(Project).filter(Project.user_id == test_user.id).delete()
    db_session.query(Gap).filter(Gap.user_id == test_user.id).delete()
    db_session.query(UserSkill).filter(UserSkill.user_id == test_user.id).delete()
    db_session.commit()
    
    s1 = get_or_create_skill(db_session, "Testing")
    s2 = get_or_create_skill(db_session, "Python")
    
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s2.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.add(Gap(user_id=test_user.id, skill_id=s1.id, actual_state="MISSING", required_state="STRONG", state_distance=3, importance_weight=1.0, severity=3.0, calculation_version="v1"))
    
    p = Project(user_id=test_user.id, github_repo_id=1, name="Proj1")
    db_session.add(p)
    db_session.commit()
    
    response = auth_client.get("/api/next-best-action")
    assert response.status_code == 200
    data = response.json()
    assert data["action_key"] == "ADD_API_TESTS"
    assert "traceability" in data
    assert data["traceability"]["gap_severity"] == 3.0

def test_dismiss_nba(auth_client, db_session, test_user):
    db_session.query(ActionHistory).filter(ActionHistory.user_id == test_user.id).delete()
    db_session.query(Recommendation).filter(Recommendation.user_id == test_user.id).delete()
    db_session.query(Project).filter(Project.user_id == test_user.id).delete()
    db_session.query(Gap).filter(Gap.user_id == test_user.id).delete()
    db_session.query(UserSkill).filter(UserSkill.user_id == test_user.id).delete()
    db_session.commit()
    
    p = Project(user_id=test_user.id, github_repo_id=1, name="Proj1")
    db_session.add(p)
    db_session.commit()
    
    # Complete an action via API
    response = auth_client.post("/api/next-best-action/dismiss", json={
        "action_key": "ADD_API_TESTS",
        "project_id": p.id
    })
    assert response.status_code == 200
    
    history = db_session.query(ActionHistory).filter(ActionHistory.user_id == test_user.id).first()
    assert history is not None
    assert history.status == ActionHistoryStatus.DISMISSED
    
    # Getting NBA should now be empty (NO_ACTION) because there's only 1 gap and it's dismissed
    response = auth_client.get("/api/next-best-action")
    assert response.status_code == 404
    assert response.json()["detail"] == "NO_ACTION"

def test_complete_nba(auth_client, db_session, test_user):
    # Needs a fresh DB state, conftest rolls back, so we have to recreate the gap?
    # Wait, the previous test was rolled back. So we do it again.
    db_session.query(ActionHistory).filter(ActionHistory.user_id == test_user.id).delete()
    db_session.query(Recommendation).filter(Recommendation.user_id == test_user.id).delete()
    db_session.query(Project).filter(Project.user_id == test_user.id).delete()
    db_session.query(Gap).filter(Gap.user_id == test_user.id).delete()
    db_session.query(UserSkill).filter(UserSkill.user_id == test_user.id).delete()
    db_session.commit()
    
    s1 = get_or_create_skill(db_session, "Testing")
    s2 = get_or_create_skill(db_session, "Python")
    
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s2.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.add(Gap(user_id=test_user.id, skill_id=s1.id, actual_state="MISSING", required_state="STRONG", state_distance=3, importance_weight=1.0, severity=3.0, calculation_version="v1"))
    
    p = Project(user_id=test_user.id, github_repo_id=1, name="Proj1")
    db_session.add(p)
    db_session.commit()
    
    response = auth_client.post("/api/next-best-action/complete", json={
        "action_key": "ADD_API_TESTS",
        "project_id": p.id
    })
    assert response.status_code == 200
    
    history = db_session.query(ActionHistory).filter(ActionHistory.user_id == test_user.id).first()
    assert history is not None
    assert history.status == ActionHistoryStatus.COMPLETED
