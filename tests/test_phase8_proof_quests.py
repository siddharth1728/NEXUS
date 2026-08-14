import pytest
from app.models.user import User, Gap, UserSkill, SkillState
from app.models.taxonomy import Skill
from app.models.project import Project, RepositorySnapshot, Artifact, RawObservation, Evidence, EvidenceType
from app.models.action import Recommendation, ActionHistory, ActionHistoryStatus
from app.config.action_catalog import get_action_catalog
from app.services.nba_engine import recalculate_next_best_action, get_available_quests, get_quest_detail, verify_quest_outcome

def get_or_create_skill(db, name, category="Backend"):
    s = db.query(Skill).filter(Skill.name == name).first()
    if not s:
        s = Skill(name=name, category=category)
        db.add(s)
        db.commit()
    return s

def clean_state(db_session, user_id):
    db_session.query(ActionHistory).filter(ActionHistory.user_id == user_id).delete()
    db_session.query(Recommendation).filter(Recommendation.user_id == user_id).delete()
    db_session.query(Project).filter(Project.user_id == user_id).delete()
    db_session.query(Gap).filter(Gap.user_id == user_id).delete()
    db_session.query(UserSkill).filter(UserSkill.user_id == user_id).delete()
    db_session.commit()

def test_gap_produces_eligible_quest(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    
    s_testing = get_or_create_skill(db_session, "Testing")
    s_python = get_or_create_skill(db_session, "Python")
    
    # Prerequisite Python=STRONG, Gap in Testing (MISSING -> STRONG)
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_python.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.add(Gap(user_id=test_user.id, skill_id=s_testing.id, actual_state=SkillState.MISSING, required_state=SkillState.STRONG, state_distance=3, importance_weight=1.0, severity=3.0, calculation_version="v1"))
    
    p = Project(user_id=test_user.id, github_repo_id=101, name="MyApiProject")
    db_session.add(p)
    db_session.commit()
    
    resp = auth_client.get("/api/quests")
    assert resp.status_code == 200
    quests = resp.json()
    assert len(quests) >= 1
    primary = quests[0]
    assert primary["action_key"] == "ADD_API_TESTS"
    assert primary["skill_name"] == "Testing"
    assert primary["project_id"] == p.id
    assert primary["is_primary"] is True

def test_no_gap_produces_no_quest(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    
    resp = auth_client.get("/api/quests")
    assert resp.status_code == 200
    assert resp.json() == []

def test_state_range_enforced(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    
    s_docker = get_or_create_skill(db_session, "Docker")
    s_python = get_or_create_skill(db_session, "Python")
    
    # Docker action ADD_DOCKER_CONTAINERIZATION has max_current_state = WEAK.
    # If the user already has DEVELOPING, it should NOT produce this quest!
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_python.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_docker.id, state=SkillState.DEVELOPING, calculation_version="v1"))
    db_session.add(Gap(user_id=test_user.id, skill_id=s_docker.id, actual_state=SkillState.DEVELOPING, required_state=SkillState.STRONG, state_distance=1, importance_weight=1.0, severity=1.0, calculation_version="v1"))
    
    p = Project(user_id=test_user.id, github_repo_id=102, name="MyService")
    db_session.add(p)
    db_session.commit()
    
    resp = auth_client.get("/api/quests")
    assert resp.status_code == 200
    docker_quests = [q for q in resp.json() if q["action_key"] == "ADD_DOCKER_CONTAINERIZATION"]
    assert len(docker_quests) == 0

def test_prerequisite_blocks_quest(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    
    s_testing = get_or_create_skill(db_session, "Testing")
    s_cicd = get_or_create_skill(db_session, "CI/CD")
    
    # CI/CD requires Testing >= WEAK. If Testing is MISSING, CI/CD quest must be blocked!
    db_session.add(Gap(user_id=test_user.id, skill_id=s_cicd.id, actual_state=SkillState.MISSING, required_state=SkillState.STRONG, state_distance=3, importance_weight=1.0, severity=3.0, calculation_version="v1"))
    p = Project(user_id=test_user.id, github_repo_id=103, name="PipelineRepo")
    db_session.add(p)
    db_session.commit()
    
    resp = auth_client.get("/api/quests")
    assert resp.status_code == 200
    cicd_quests = [q for q in resp.json() if q["action_key"] == "ADD_CI_PIPELINE"]
    assert len(cicd_quests) == 0

def test_project_requirement_enforced(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    
    s_testing = get_or_create_skill(db_session, "Testing")
    s_python = get_or_create_skill(db_session, "Python")
    
    # Testing requires an existing project. With 0 projects, it must not be available.
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_python.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.add(Gap(user_id=test_user.id, skill_id=s_testing.id, actual_state=SkillState.MISSING, required_state=SkillState.STRONG, state_distance=3, importance_weight=1.0, severity=3.0, calculation_version="v1"))
    db_session.commit()
    
    resp = auth_client.get("/api/quests")
    assert resp.status_code == 200
    testing_quests = [q for q in resp.json() if q["action_key"] == "ADD_API_TESTS"]
    assert len(testing_quests) == 0

def test_begin_and_complete_lifecycle(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    
    s_testing = get_or_create_skill(db_session, "Testing")
    s_python = get_or_create_skill(db_session, "Python")
    
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_python.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.add(Gap(user_id=test_user.id, skill_id=s_testing.id, actual_state=SkillState.MISSING, required_state=SkillState.STRONG, state_distance=3, importance_weight=1.0, severity=3.0, calculation_version="v1"))
    p = Project(user_id=test_user.id, github_repo_id=104, name="TestApi")
    db_session.add(p)
    db_session.commit()
    
    # 1. Begin Quest
    begin_resp = auth_client.post("/api/quests/begin", json={
        "action_key": "ADD_API_TESTS",
        "project_id": p.id
    })
    assert begin_resp.status_code == 200
    
    history_started = db_session.query(ActionHistory).filter(
        ActionHistory.user_id == test_user.id,
        ActionHistory.action_key == "ADD_API_TESTS"
    ).first()
    assert history_started.status == ActionHistoryStatus.STARTED
    
    # 2. Mark Complete
    comp_resp = auth_client.post("/api/quests/complete", json={
        "action_key": "ADD_API_TESTS",
        "project_id": p.id
    })
    assert comp_resp.status_code == 200
    assert "Sync your repository" in comp_resp.json()["message"]

def test_critical_truth_completion_does_not_change_skill_or_gap(auth_client, db_session, test_user):
    """
    CRITICAL TRUTH CONTRACT:
    Marking a quest complete MUST NOT change UserSkill, create Evidence, or close Gap!
    """
    clean_state(db_session, test_user.id)
    
    s_testing = get_or_create_skill(db_session, "Testing")
    s_python = get_or_create_skill(db_session, "Python")
    
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_python.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s_testing.id, state=SkillState.MISSING, calculation_version="v1"))
    db_session.add(Gap(user_id=test_user.id, skill_id=s_testing.id, actual_state=SkillState.MISSING, required_state=SkillState.STRONG, state_distance=3, importance_weight=1.0, severity=3.0, calculation_version="v1"))
    p = Project(user_id=test_user.id, github_repo_id=105, name="TruthRepo")
    db_session.add(p)
    db_session.commit()
    
    auth_client.post("/api/quests/complete", json={
        "action_key": "ADD_API_TESTS",
        "project_id": p.id
    })
    
    # UserSkill state MUST still be MISSING
    skill = db_session.query(UserSkill).filter(UserSkill.user_id == test_user.id, UserSkill.skill_id == s_testing.id).first()
    assert skill.state == SkillState.MISSING
    
    # Gap MUST still exist
    gap = db_session.query(Gap).filter(Gap.user_id == test_user.id, Gap.skill_id == s_testing.id).first()
    assert gap is not None
    assert gap.actual_state == SkillState.MISSING

def test_cross_user_project_protection(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    
    # Other user and project
    other_user = User(email="other_quest_user@example.com", password_hash="pw")
    db_session.add(other_user)
    db_session.commit()
    
    other_project = Project(user_id=other_user.id, github_repo_id=999, name="PrivateRepo")
    db_session.add(other_project)
    db_session.commit()
    
    # Attempting to begin or complete quest on other user's project must return 404
    resp = auth_client.post("/api/quests/begin", json={
        "action_key": "ADD_API_TESTS",
        "project_id": other_project.id
    })
    assert resp.status_code == 404

def test_quest_verification_outcome(auth_client, db_session, test_user):
    clean_state(db_session, test_user.id)
    
    s_testing = get_or_create_skill(db_session, "Testing")
    
    # Before evidence: not verified
    resp = auth_client.get("/api/quests/ADD_API_TESTS/verification")
    assert resp.status_code == 200
    v_data = resp.json()
    assert v_data["verified"] is False
    assert "Not yet verified" in v_data["explanation"]
