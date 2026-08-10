import pytest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from app.models.user import User, Gap, UserSkill, SkillState
from app.models.taxonomy import Skill
from app.models.project import Project, Evidence, Artifact, RawObservation, EvidenceType
from app.models.action import Recommendation, ActionHistory, ActionHistoryStatus
from app.services.nba_engine import recalculate_next_best_action
from app.config.action_catalog import get_action_catalog, ActionDefinition

def test_no_gaps_returns_none(db_session, test_user):
    # Ensure no gaps
    db_session.query(Gap).delete()
    db_session.commit()
    
    rec = recalculate_next_best_action(test_user.id, db_session)
    assert rec is None

def get_or_create_skill(db, name, category="Cat"):
    s = db.query(Skill).filter(Skill.name == name).first()
    if not s:
        s = Skill(name=name, category=category)
        db.add(s)
        db.commit()
    return s

def test_highest_value_gap_selected(db_session, test_user):
    db_session.query(ActionHistory).filter(ActionHistory.user_id == test_user.id).delete()
    db_session.query(Recommendation).filter(Recommendation.user_id == test_user.id).delete()
    db_session.query(Project).filter(Project.user_id == test_user.id).delete()
    db_session.query(Gap).filter(Gap.user_id == test_user.id).delete()
    db_session.query(UserSkill).filter(UserSkill.user_id == test_user.id).delete()
    db_session.commit()

    s1 = get_or_create_skill(db_session, "Testing")
    s2 = get_or_create_skill(db_session, "REST APIs")
    s3 = get_or_create_skill(db_session, "Python")
    
    # Prerequisite UserSkill
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s3.id, state=SkillState.STRONG, calculation_version="v1"))
    
    # Setup Gaps
    gap1 = Gap(user_id=test_user.id, skill_id=s1.id, actual_state="MISSING", required_state="STRONG", state_distance=3, importance_weight=1.0, severity=3.0, calculation_version="v1")
    gap2 = Gap(user_id=test_user.id, skill_id=s2.id, actual_state="MISSING", required_state="STRONG", state_distance=3, importance_weight=2.0, severity=6.0, calculation_version="v1")
    db_session.add_all([gap1, gap2])
    db_session.commit()
    
    # Setup a project
    p = Project(user_id=test_user.id, github_repo_id=1, name="Proj1")
    db_session.add(p)
    db_session.commit()
    
    rec = recalculate_next_best_action(test_user.id, db_session)
    assert rec is not None
    # Action for REST APIs has higher severity gap (6.0 vs 3.0), but REST APIs has NO project requirement (CREATE_NEW_API_PROJECT) which gives 1.0 proj multiplier. 
    # Testing has 3.0 severity, requires project (1.10 proj multiplier).
    # REST API Effort=3 (mult=0.577), Testing Effort=2 (mult=0.707).
    # REST API Priority = 6.0 * 1.0 * 0.577 * 1.0 = 3.46
    # Testing Priority = 3.0 * 1.0 * 0.707 * 1.10 = 2.33
    # Therefore REST APIs should win.
    assert rec.action_key == "CREATE_NEW_API_PROJECT"
    assert rec.priority_score > 3.0

def test_prerequisites_block_invalid_actions(db_session, test_user):
    db_session.query(UserSkill).delete() # No python prereq!
    db_session.query(Gap).delete()
    
    s2 = get_or_create_skill(db_session, "REST APIs")
    
    gap2 = Gap(user_id=test_user.id, skill_id=s2.id, actual_state="MISSING", required_state="STRONG", state_distance=3, importance_weight=2.0, severity=6.0, calculation_version="v1")
    db_session.add(gap2)
    db_session.commit()
    
    # REST APIs requires Python >= WEAK. Since we deleted UserSkill, it is MISSING.
    rec = recalculate_next_best_action(test_user.id, db_session)
    assert rec is None # No eligible candidates

def test_temporary_suppression(db_session, test_user):
    db_session.query(ActionHistory).filter(ActionHistory.user_id == test_user.id).delete()
    db_session.query(Recommendation).filter(Recommendation.user_id == test_user.id).delete()
    db_session.query(Project).filter(Project.user_id == test_user.id).delete()
    db_session.query(Gap).filter(Gap.user_id == test_user.id).delete()
    db_session.query(UserSkill).filter(UserSkill.user_id == test_user.id).delete()
    db_session.commit()
    
    s1 = get_or_create_skill(db_session, "Testing")
    s3 = get_or_create_skill(db_session, "Python")
    
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s3.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.add(Gap(user_id=test_user.id, skill_id=s1.id, actual_state="MISSING", required_state="STRONG", state_distance=3, importance_weight=1.0, severity=3.0, calculation_version="v1"))
    
    p = Project(user_id=test_user.id, github_repo_id=1, name="Proj1")
    db_session.add(p)
    db_session.commit()
    
    rec = recalculate_next_best_action(test_user.id, db_session)
    assert rec is not None
    assert rec.action_key == "ADD_API_TESTS"
    
    # Now simulate completing it
    history = ActionHistory(user_id=test_user.id, action_key="ADD_API_TESTS", project_id=p.id, status=ActionHistoryStatus.COMPLETED, created_at=datetime.now(timezone.utc))
    db_session.add(history)
    db_session.commit()
    
    rec2 = recalculate_next_best_action(test_user.id, db_session)
    assert rec2 is None # Suppressed!
    
    # Move history back 31 days
    history.created_at = datetime.now(timezone.utc) - timedelta(days=31)
    db_session.commit()
    
    rec3 = recalculate_next_best_action(test_user.id, db_session)
    assert rec3 is not None # Unsuppressed!

def test_evidence_improvement_potential_anti_inflation(db_session, test_user):
    db_session.query(ActionHistory).filter(ActionHistory.user_id == test_user.id).delete()
    db_session.query(Recommendation).filter(Recommendation.user_id == test_user.id).delete()
    db_session.query(Project).filter(Project.user_id == test_user.id).delete()
    db_session.query(Gap).filter(Gap.user_id == test_user.id).delete()
    db_session.query(UserSkill).filter(UserSkill.user_id == test_user.id).delete()
    db_session.commit()
    
    s1 = get_or_create_skill(db_session, "Testing")
    s3 = get_or_create_skill(db_session, "Python")
    
    db_session.add(UserSkill(user_id=test_user.id, skill_id=s3.id, state=SkillState.STRONG, calculation_version="v1"))
    db_session.add(Gap(user_id=test_user.id, skill_id=s1.id, actual_state="MISSING", required_state="STRONG", state_distance=3, importance_weight=1.0, severity=3.0, calculation_version="v1"))
    
    p = Project(user_id=test_user.id, github_repo_id=1, name="Proj1")
    db_session.add(p)
    db_session.commit()
    
    # First recalc, should be high priority
    rec1 = recalculate_next_best_action(test_user.id, db_session)
    score1 = rec1.priority_score
    
    # Add fake evidence that saturates the capacity (1.5 max)
    # We need RawObservation and Artifact
    from app.models.project import RepositorySnapshot
    snap = RepositorySnapshot(project_id=p.id, status="COMPLETED")
    db_session.add(snap)
    db_session.commit()
    
    art = Artifact(snapshot_id=snap.id, file_path="test_app.py", type="Test file")
    db_session.add(art)
    db_session.commit()
    
    obs = RawObservation(artifact_id=art.id, observation_text="Has tests")
    db_session.add(obs)
    db_session.commit()
    
    ev = Evidence(raw_observation_id=obs.id, type=EvidenceType.TESTING, quality_score=1.5, freshness_weight=1.0)
    db_session.add(ev)
    db_session.commit()
    
    rec2 = recalculate_next_best_action(test_user.id, db_session)
    # Should be None because EvidenceType capacity is full (1.5), so potential is 0.0 -> Rejected
    assert rec2 is None
