from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.profile import StudentProfile
from app.models.taxonomy import TargetRoleSkill
from app.models.user import UserSkill, Gap
import logging

logger = logging.getLogger(__name__)

CALCULATION_VERSION = "gap_v1"

STATE_ORDER = {
    "MISSING": 0,
    "WEAK": 1,
    "DEVELOPING": 2,
    "STRONG": 3
}

def recalculate_user_gaps(user_id: int, db: Session) -> None:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    
    if not profile or not profile.target_role_id:
        # User has no target role, so they can't have gaps. Remove any existing gaps.
        db.query(Gap).filter(Gap.user_id == user_id).delete()
        db.commit()
        return

    # 3. Find all TargetRoleSkill requirements
    required_skills = db.query(TargetRoleSkill).filter(TargetRoleSkill.target_role_id == profile.target_role_id).all()
    
    # 4. Find the user's UserSkill states
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    user_skill_states = {us.skill_id: us.state.value for us in user_skills}
    
    processed_skill_ids = set()
    
    for req in required_skills:
        skill_id = req.skill_id
        processed_skill_ids.add(skill_id)
        
        # 5. Treat missing UserSkill as MISSING
        actual_state_str = user_skill_states.get(skill_id, "MISSING")
        required_state_str = req.minimum_expected_state
        
        actual_value = STATE_ORDER.get(actual_state_str, 0)
        required_value = STATE_ORDER.get(required_state_str, 0)
        
        # 6. Compare actual vs required
        if actual_value < required_value:
            # 7. Create gaps only where actual < required
            state_distance = required_value - actual_value
            severity = state_distance * req.importance_weight
            
            gap = db.query(Gap).filter(Gap.user_id == user_id, Gap.skill_id == skill_id).first()
            if not gap:
                gap = Gap(user_id=user_id, skill_id=skill_id)
                db.add(gap)
            
            # 8. Rebuild/upsert derived Gap records deterministically
            gap.actual_state = actual_state_str
            gap.required_state = required_state_str
            gap.state_distance = state_distance
            gap.importance_weight = req.importance_weight
            gap.severity = severity
            gap.calculated_at = func.now()
            gap.calculation_version = CALCULATION_VERSION
        else:
            # 9. Remove obsolete derived gaps when the user improves
            db.query(Gap).filter(Gap.user_id == user_id, Gap.skill_id == skill_id).delete()
            
    # Delete gaps for skills no longer required by the role
    db.query(Gap).filter(Gap.user_id == user_id, ~Gap.skill_id.in_(processed_skill_ids if processed_skill_ids else [0])).delete(synchronize_session=False)
    
    db.commit()
