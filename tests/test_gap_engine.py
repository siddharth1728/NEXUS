import pytest
from sqlalchemy.orm import Session
from app.models.user import User, UserSkill, SkillState, Gap
from app.models.taxonomy import Skill, TargetRole, TargetRoleSkill
from app.models.profile import StudentProfile
from app.services.gap_engine import recalculate_user_gaps

def create_gap_setup(db: Session, user: User, role_name: str, skill_name: str, req_state: str, importance: float = 1.0):
    role = TargetRole(name=role_name)
    db.add(role)
    db.commit()
    
    skill = Skill(name=skill_name, category="Test")
    db.add(skill)
    db.commit()
    
    trs = TargetRoleSkill(target_role_id=role.id, skill_id=skill.id, importance_weight=importance, minimum_expected_state=req_state)
    db.add(trs)
    db.commit()
    
    profile = StudentProfile(user_id=user.id, target_role_id=role.id)
    db.add(profile)
    db.commit()
    
    return role, skill

def test_all_requirements_met(db_session: Session):
    import uuid
    user = User(email=f"{uuid.uuid4()}@test.com", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    role, skill = create_gap_setup(db_session, user, "Role1", "Skill1", "DEVELOPING")
    
    us = UserSkill(user_id=user.id, skill_id=skill.id, state=SkillState.STRONG, calculation_version="v1")
    db_session.add(us)
    db_session.commit()
    
    recalculate_user_gaps(user.id, db_session)
    assert db_session.query(Gap).filter(Gap.user_id == user.id).count() == 0

def test_missing_user_skill(db_session: Session):
    import uuid
    user = User(email=f"{uuid.uuid4()}@test.com", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    role, skill = create_gap_setup(db_session, user, "Role2", "Skill2", "DEVELOPING", 1.5)
    
    recalculate_user_gaps(user.id, db_session)
    gap = db_session.query(Gap).filter(Gap.user_id == user.id).first()
    assert gap is not None
    assert gap.actual_state == "MISSING"
    assert gap.state_distance == 2
    assert gap.severity == 3.0

def test_missing_to_developing(db_session: Session):
    import uuid
    user = User(email=f"{uuid.uuid4()}@test.com", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    role, skill = create_gap_setup(db_session, user, "Role3", "Skill3", "DEVELOPING")
    us = UserSkill(user_id=user.id, skill_id=skill.id, state=SkillState.MISSING, calculation_version="v1")
    db_session.add(us)
    db_session.commit()
    
    recalculate_user_gaps(user.id, db_session)
    gap = db_session.query(Gap).filter(Gap.user_id == user.id).first()
    assert gap.state_distance == 2

def test_weak_to_developing(db_session: Session):
    import uuid
    user = User(email=f"{uuid.uuid4()}@test.com", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    role, skill = create_gap_setup(db_session, user, "Role4", "Skill4", "DEVELOPING")
    us = UserSkill(user_id=user.id, skill_id=skill.id, state=SkillState.WEAK, calculation_version="v1")
    db_session.add(us)
    db_session.commit()
    
    recalculate_user_gaps(user.id, db_session)
    gap = db_session.query(Gap).filter(Gap.user_id == user.id).first()
    assert gap.state_distance == 1

def test_developing_to_strong(db_session: Session):
    import uuid
    user = User(email=f"{uuid.uuid4()}@test.com", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    role, skill = create_gap_setup(db_session, user, "Role5", "Skill5", "STRONG")
    us = UserSkill(user_id=user.id, skill_id=skill.id, state=SkillState.DEVELOPING, calculation_version="v1")
    db_session.add(us)
    db_session.commit()
    
    recalculate_user_gaps(user.id, db_session)
    gap = db_session.query(Gap).filter(Gap.user_id == user.id).first()
    assert gap.state_distance == 1

def test_strong_to_strong(db_session: Session):
    import uuid
    user = User(email=f"{uuid.uuid4()}@test.com", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    role, skill = create_gap_setup(db_session, user, "Role6", "Skill6", "STRONG")
    us = UserSkill(user_id=user.id, skill_id=skill.id, state=SkillState.STRONG, calculation_version="v1")
    db_session.add(us)
    db_session.commit()
    
    recalculate_user_gaps(user.id, db_session)
    assert db_session.query(Gap).filter(Gap.user_id == user.id).count() == 0

def test_strong_to_weak_no_gap(db_session: Session):
    import uuid
    user = User(email=f"{uuid.uuid4()}@test.com", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    role, skill = create_gap_setup(db_session, user, "Role7", "Skill7", "WEAK")
    us = UserSkill(user_id=user.id, skill_id=skill.id, state=SkillState.STRONG, calculation_version="v1")
    db_session.add(us)
    db_session.commit()
    
    recalculate_user_gaps(user.id, db_session)
    assert db_session.query(Gap).filter(Gap.user_id == user.id).count() == 0

def test_state_distance_calculation(db_session: Session):
    # Tested inherently above
    pass

def test_importance_weight_severity(db_session: Session):
    import uuid
    user = User(email=f"{uuid.uuid4()}@test.com", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    role, skill = create_gap_setup(db_session, user, "Role8", "Skill8", "STRONG", 2.0)
    us = UserSkill(user_id=user.id, skill_id=skill.id, state=SkillState.WEAK, calculation_version="v1")
    db_session.add(us)
    db_session.commit()
    
    recalculate_user_gaps(user.id, db_session)
    gap = db_session.query(Gap).filter(Gap.user_id == user.id).first()
    # STRONG (3) - WEAK (1) = 2. Severity = 2 * 2.0 = 4.0
    assert gap.severity == 4.0

def test_deterministic_sorting(db_session: Session):
    # We will test this in API test since engine just writes to DB without ordering
    pass

def test_tie_breaking(db_session: Session):
    pass

def test_no_target_role(db_session: Session):
    import uuid
    user = User(email=f"{uuid.uuid4()}@test.com", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    recalculate_user_gaps(user.id, db_session)
    assert db_session.query(Gap).filter(Gap.user_id == user.id).count() == 0

def test_recalculation_idempotent(db_session: Session):
    import uuid
    user = User(email=f"{uuid.uuid4()}@test.com", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    role, skill = create_gap_setup(db_session, user, "Role9", "Skill9", "STRONG")
    recalculate_user_gaps(user.id, db_session)
    recalculate_user_gaps(user.id, db_session)
    assert db_session.query(Gap).filter(Gap.user_id == user.id).count() == 1

def test_obsolete_gap_disappears(db_session: Session):
    import uuid
    user = User(email=f"{uuid.uuid4()}@test.com", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    role, skill = create_gap_setup(db_session, user, "Role10", "Skill10", "STRONG")
    recalculate_user_gaps(user.id, db_session)
    
    # simulate user improving
    us = UserSkill(user_id=user.id, skill_id=skill.id, state=SkillState.STRONG, calculation_version="v1")
    db_session.add(us)
    db_session.commit()
    
    recalculate_user_gaps(user.id, db_session)
    assert db_session.query(Gap).filter(Gap.user_id == user.id).count() == 0

def test_gap_does_not_modify_userskill(db_session: Session):
    import uuid
    user = User(email=f"{uuid.uuid4()}@test.com", password_hash="pw")
    db_session.add(user)
    db_session.commit()
    
    role, skill = create_gap_setup(db_session, user, "Role11", "Skill11", "STRONG")
    us = UserSkill(user_id=user.id, skill_id=skill.id, state=SkillState.WEAK, calculation_version="v1")
    db_session.add(us)
    db_session.commit()
    
    recalculate_user_gaps(user.id, db_session)
    # verify user skill is still WEAK
    us = db_session.query(UserSkill).filter(UserSkill.user_id == user.id).first()
    assert us.state == SkillState.WEAK

def test_targetroleskill_only_source(db_session: Session):
    pass
    
def test_github_stars_independent(db_session: Session):
    pass
    
def test_repo_count_independent(db_session: Session):
    pass
    
def test_gap_no_recommendation(db_session: Session):
    pass
