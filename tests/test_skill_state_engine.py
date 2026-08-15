import pytest
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.user import User, UserSkill, SkillState
from app.models.taxonomy import Skill
from app.models.project import Project, RepositorySnapshot, Artifact, RawObservation, Evidence, EvidenceType, EvidenceSkill
from app.services.skill_state_engine import recalculate_user_skills

import random

def create_test_setup(db: Session, user: User, skill_name: str = "TestSkill") -> tuple:
    skill = db.query(Skill).filter(Skill.name == skill_name).first()
    if not skill:
        skill = Skill(name=skill_name, category="Test")
        db.add(skill)
        
    project = Project(user_id=user.id, github_repo_id=random.randint(100000, 99999999), name="test_repo")
    db.add(project)
    db.commit()
    
    snapshot = RepositorySnapshot(project_id=project.id, captured_at=datetime.now(timezone.utc))
    db.add(snapshot)
    db.commit()
    
    return project, snapshot, skill

def create_evidence(db, snapshot, skill, type=EvidenceType.API, artifact_path="app.py", quality=1.0, freshness=1.0):
    artifact = db.query(Artifact).filter(Artifact.snapshot_id==snapshot.id, Artifact.file_path==artifact_path).first()
    if not artifact:
        artifact = Artifact(snapshot_id=snapshot.id, file_path=artifact_path, type="code")
        db.add(artifact)
        db.commit()
        
    obs = RawObservation(artifact_id=artifact.id, observation_text="test obs")
    db.add(obs)
    db.commit()
    
    ev = Evidence(raw_observation_id=obs.id, type=type, quality_score=quality, freshness_weight=freshness)
    db.add(ev)
    db.commit()
    
    ev_skill = EvidenceSkill(evidence_id=ev.id, skill_id=skill.id)
    db.add(ev_skill)
    db.commit()
    return ev

def test_no_evidence_missing(db_session: Session):
    # Create fresh user to guarantee zero evidence
    import uuid
    fresh_user = User(email=f"fresh_{uuid.uuid4()}@example.com", password_hash="pw")
    db_session.add(fresh_user)
    db_session.commit()
    
    # Test 1, 15, 16, 17
    recalculate_user_skills(fresh_user.id, db_session)
    assert db_session.query(UserSkill).filter(UserSkill.user_id == fresh_user.id).count() == 0

def test_one_weak_evidence(db_session: Session, test_user: User):
    # Test 2
    _, snap, skill = create_test_setup(db_session, test_user, "Skill2")
    create_evidence(db_session, snap, skill, quality=0.5, freshness=1.0)
    recalculate_user_skills(test_user.id, db_session)
    us = db_session.query(UserSkill).filter(UserSkill.user_id==test_user.id, UserSkill.skill_id==skill.id).first()
    assert us.state == SkillState.WEAK

def test_partial_evidence(db_session: Session, test_user: User):
    # Test 3
    _, snap, skill = create_test_setup(db_session, test_user, "Skill3")
    create_evidence(db_session, snap, skill, type=EvidenceType.API, artifact_path="1.py", quality=0.8, freshness=1.0)
    create_evidence(db_session, snap, skill, type=EvidenceType.TESTING, artifact_path="2.py", quality=0.8, freshness=1.0)
    recalculate_user_skills(test_user.id, db_session)
    us = db_session.query(UserSkill).filter(UserSkill.user_id==test_user.id, UserSkill.skill_id==skill.id).first()
    assert us.state == SkillState.DEVELOPING

def test_broad_strong_evidence(db_session: Session, test_user: User):
    # Test 4, 8, 9
    _, snap, skill = create_test_setup(db_session, test_user, "Skill4")
    create_evidence(db_session, snap, skill, type=EvidenceType.API, artifact_path="1.py", quality=0.9, freshness=1.0)
    create_evidence(db_session, snap, skill, type=EvidenceType.TESTING, artifact_path="2.py", quality=0.9, freshness=1.0)
    create_evidence(db_session, snap, skill, type=EvidenceType.DATABASE, artifact_path="3.py", quality=0.9, freshness=1.0)
    create_evidence(db_session, snap, skill, type=EvidenceType.ARCHITECTURE, artifact_path="4.py", quality=0.9, freshness=1.0)
    recalculate_user_skills(test_user.id, db_session)
    us = db_session.query(UserSkill).filter(UserSkill.user_id==test_user.id, UserSkill.skill_id==skill.id).first()
    assert us.state == SkillState.STRONG

def test_one_evidence_cannot_be_strong(db_session: Session, test_user: User):
    # Test 5
    _, snap, skill = create_test_setup(db_session, test_user, "Skill5")
    create_evidence(db_session, snap, skill, quality=1.0, freshness=1.0)
    recalculate_user_skills(test_user.id, db_session)
    us = db_session.query(UserSkill).filter(UserSkill.user_id==test_user.id, UserSkill.skill_id==skill.id).first()
    assert us.state == SkillState.WEAK

def test_artifact_cap(db_session: Session, test_user: User):
    # Test 6
    _, snap, skill = create_test_setup(db_session, test_user, "Skill6")
    for i in range(10):
        create_evidence(db_session, snap, skill, type=EvidenceType.API, artifact_path="huge_file.py", quality=0.9, freshness=1.0)
    recalculate_user_skills(test_user.id, db_session)
    us = db_session.query(UserSkill).filter(UserSkill.user_id==test_user.id, UserSkill.skill_id==skill.id).first()
    assert us.state != SkillState.STRONG

def test_type_cap(db_session: Session, test_user: User):
    # Test 7
    _, snap, skill = create_test_setup(db_session, test_user, "Skill7")
    for i in range(10):
        create_evidence(db_session, snap, skill, type=EvidenceType.API, artifact_path=f"file{i}.py", quality=0.9, freshness=1.0)
    recalculate_user_skills(test_user.id, db_session)
    us = db_session.query(UserSkill).filter(UserSkill.user_id==test_user.id, UserSkill.skill_id==skill.id).first()
    assert us.state == SkillState.DEVELOPING

def test_freshness_changes_contribution(db_session: Session, test_user: User):
    # Test 10
    _, snap, skill = create_test_setup(db_session, test_user, "Skill10")
    create_evidence(db_session, snap, skill, quality=1.0, freshness=0.1) # 0.1 * 1.0 < 0.5 threshold
    recalculate_user_skills(test_user.id, db_session)
    us = db_session.query(UserSkill).filter(UserSkill.user_id==test_user.id, UserSkill.skill_id==skill.id).first()
    assert us.state == SkillState.MISSING

def test_deterministic_and_idempotent(db_session: Session, test_user: User):
    # Test 12, 13
    _, snap, skill = create_test_setup(db_session, test_user, "Skill12")
    create_evidence(db_session, snap, skill, quality=0.8, freshness=1.0)
    recalculate_user_skills(test_user.id, db_session)
    us1 = db_session.query(UserSkill).filter(UserSkill.user_id==test_user.id, UserSkill.skill_id==skill.id).first().state
    recalculate_user_skills(test_user.id, db_session)
    us2 = db_session.query(UserSkill).filter(UserSkill.user_id==test_user.id, UserSkill.skill_id==skill.id).first().state
    assert us1 == us2

def test_removing_evidence_missing(db_session: Session, test_user: User):
    # Test 11, 14, 18
    _, snap, skill = create_test_setup(db_session, test_user, "Skill14")
    ev = create_evidence(db_session, snap, skill, quality=0.8, freshness=1.0)
    recalculate_user_skills(test_user.id, db_session)
    
    # Remove the evidence skill link to simulate no valid evidence
    db_session.query(EvidenceSkill).delete()
    db_session.commit()
    
    recalculate_user_skills(test_user.id, db_session)
    us = db_session.query(UserSkill).filter(UserSkill.user_id==test_user.id, UserSkill.skill_id==skill.id).first()
    assert us.state == SkillState.MISSING

def test_userskill_unique_constraint(db_session: Session, test_user: User):
    # Test 19
    from sqlalchemy.exc import IntegrityError
    _, snap, skill = create_test_setup(db_session, test_user, "Skill19")
    us1 = UserSkill(user_id=test_user.id, skill_id=skill.id, state=SkillState.MISSING, calculation_version="v1")
    db_session.add(us1)
    db_session.commit()
    us2 = UserSkill(user_id=test_user.id, skill_id=skill.id, state=SkillState.WEAK, calculation_version="v1")
    db_session.add(us2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

def test_history_integrity(db_session: Session, test_user: User):
    from app.models.user import UserSkillHistory
    
    # 1. First calculation -> previous_state = NULL
    _, snap1, skill = create_test_setup(db_session, test_user, "HistorySkill")
    create_evidence(db_session, snap1, skill, quality=0.8, freshness=1.0)
    recalculate_user_skills(test_user.id, db_session, snap1.id)
    
    history_rows = db_session.query(UserSkillHistory).filter(UserSkillHistory.user_id == test_user.id, UserSkillHistory.skill_id == skill.id).order_by(UserSkillHistory.id).all()
    assert len(history_rows) == 1
    assert history_rows[0].previous_state is None
    assert history_rows[0].new_state == SkillState.WEAK.value
    assert history_rows[0].snapshot_id == snap1.id
    
    # 2. Same state recalculation -> no new history row
    recalculate_user_skills(test_user.id, db_session, snap1.id)
    history_rows = db_session.query(UserSkillHistory).filter(UserSkillHistory.user_id == test_user.id, UserSkillHistory.skill_id == skill.id).all()
    assert len(history_rows) == 1
    
    # 3. WEAK -> DEVELOPING -> exactly one row
    _, snap2, _ = create_test_setup(db_session, test_user, "HistorySkill")
    create_evidence(db_session, snap2, skill, type=EvidenceType.TESTING, artifact_path="test2.py", quality=0.8, freshness=1.0)
    recalculate_user_skills(test_user.id, db_session, snap2.id)
    
    history_rows = db_session.query(UserSkillHistory).filter(UserSkillHistory.user_id == test_user.id, UserSkillHistory.skill_id == skill.id).order_by(UserSkillHistory.id).all()
    assert len(history_rows) == 2
    assert history_rows[1].previous_state == SkillState.WEAK.value
    assert history_rows[1].new_state == SkillState.DEVELOPING.value
    assert history_rows[1].snapshot_id == snap2.id

def test_history_user_isolation(db_session: Session, test_user: User):
    from app.models.user import UserSkillHistory
    import uuid
    user2 = User(email=f"user2_{uuid.uuid4()}@example.com", password_hash="pw")
    db_session.add(user2)
    db_session.commit()
    
    _, snap1, skill = create_test_setup(db_session, test_user, "IsoSkill")
    create_evidence(db_session, snap1, skill, quality=0.8, freshness=1.0)
    recalculate_user_skills(test_user.id, db_session, snap1.id)
    
    _, snap2, _ = create_test_setup(db_session, user2, "IsoSkill")
    create_evidence(db_session, snap2, skill, quality=0.8, freshness=1.0)
    recalculate_user_skills(user2.id, db_session, snap2.id)
    
    history_user1 = db_session.query(UserSkillHistory).filter(UserSkillHistory.user_id == test_user.id, UserSkillHistory.skill_id == skill.id).all()
    history_user2 = db_session.query(UserSkillHistory).filter(UserSkillHistory.user_id == user2.id, UserSkillHistory.skill_id == skill.id).all()
    
    assert len(history_user1) == 1
    assert len(history_user2) == 1
    assert history_user1[0].user_id == test_user.id
    assert history_user2[0].user_id == user2.id

