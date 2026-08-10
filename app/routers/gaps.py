from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User, Gap
from app.models.taxonomy import Skill

router = APIRouter()

@router.get("/gaps", tags=["Gaps"])
def get_user_gaps(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Sort gaps by: 1. severity DESC, 2. importance_weight DESC, 3. required_state_value DESC, 4. skill_id ASC
    # We don't have required_state_value stored as an int in Gap, but we can derive it or just join with TargetRoleSkill if needed.
    # Actually, we can use a CASE statement to order by required_state, but the prompt says:
    # "3. required_state_value DESC"
    # To do that efficiently, we can do it in memory or with SQL case.
    # Let's do it with SQL CASE.
    
    from sqlalchemy import case
    
    state_order_case = case(
        {"STRONG": 3, "DEVELOPING": 2, "WEAK": 1, "MISSING": 0},
        value=Gap.required_state,
        else_=-1
    )
    
    gaps = (
        db.query(Gap)
        .filter(Gap.user_id == current_user.id)
        .order_by(
            Gap.severity.desc(),
            Gap.importance_weight.desc(),
            state_order_case.desc(),
            Gap.skill_id.asc()
        )
        .all()
    )
    
    return [
        {
            "skill": gap.skill.name,
            "actual_state": gap.actual_state,
            "required_state": gap.required_state,
            "state_distance": gap.state_distance,
            "importance_weight": gap.importance_weight,
            "severity": gap.severity
        } for gap in gaps
    ]
