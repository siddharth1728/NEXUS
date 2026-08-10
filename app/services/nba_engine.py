import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import Gap, UserSkill, SkillState
from app.models.taxonomy import Skill
from app.models.project import Project, Evidence, Artifact, RawObservation, EvidenceType
from app.models.action import Recommendation, ActionHistory, ActionHistoryStatus
from app.config.action_catalog import get_action_catalog, ActionDefinition

MAX_CONTRIBUTION_PER_EVIDENCE_TYPE = 1.5
MAX_CONTRIBUTION_PER_ARTIFACT = 2.0
SUPPRESSION_DAYS = 30
NBA_CALCULATION_VERSION = "nba_v1"

# State mapping helper
def state_value(state_str: str) -> int:
    state_map = {
        SkillState.MISSING: 0,
        SkillState.WEAK: 1,
        SkillState.DEVELOPING: 2,
        SkillState.STRONG: 3,
    }
    # Handle both enum values and string values
    return state_map.get(state_str, 0)

@dataclass
class Candidate:
    action: ActionDefinition
    gap: Gap
    project_id: Optional[int]
    project_name: Optional[str]
    evidence_potential: float
    effort_multiplier: float
    project_context_multiplier: float
    priority_score: float

def get_skill_map_by_name(user_id: int, db: Session) -> Dict[str, UserSkill]:
    """Returns a dict mapping skill names to UserSkill objects for the user."""
    user_skills = db.query(UserSkill).join(Skill).filter(UserSkill.user_id == user_id).all()
    return {us.skill.name: us for us in user_skills}

def get_skill_map_by_id(user_id: int, db: Session) -> Dict[int, UserSkill]:
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    return {us.skill_id: us for us in user_skills}

def is_temporarily_suppressed(user_id: int, action_key: str, project_id: Optional[int], db: Session) -> bool:
    """Check if the action was completed or dismissed in the last 30 days."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=SUPPRESSION_DAYS)
    
    query = db.query(ActionHistory).filter(
        ActionHistory.user_id == user_id,
        ActionHistory.action_key == action_key,
        ActionHistory.created_at >= cutoff_date
    )
    
    if project_id is not None:
        query = query.filter(ActionHistory.project_id == project_id)
        
    recent_history = query.first()
    return recent_history is not None

def calculate_evidence_potential(user_id: int, action: ActionDefinition, project_id: Optional[int], db: Session) -> float:
    """
    Evaluates Phase 4 anti-inflation rules.
    If the user has 1.5 contribution for the expected type -> LOW/NONE potential.
    If the project has maxed artifacts -> LOW potential.
    HIGH=1.0, MEDIUM=0.7, LOW=0.3, NONE=0.0
    """
    if not action.expected_evidence_types:
        return 1.0 # If no specific evidence type expected, assume HIGH.

    # Check EvidenceType capacity globally for the user
    # Fetch all evidence for the user
    from app.models.project import RepositorySnapshot
    user_evidence = db.query(Evidence).join(RawObservation).join(Artifact).join(RepositorySnapshot).join(Project).filter(
        Project.user_id == user_id
    ).all()
    
    total_type_contrib = 0.0
    for ev in user_evidence:
        if ev.type in action.expected_evidence_types:
            contrib = ev.quality_score * ev.freshness_weight
            if contrib >= 0.5:
                total_type_contrib += min(contrib, MAX_CONTRIBUTION_PER_EVIDENCE_TYPE)

    if total_type_contrib >= MAX_CONTRIBUTION_PER_EVIDENCE_TYPE:
        return 0.0 # NONE (no headroom)
        
    if total_type_contrib >= (MAX_CONTRIBUTION_PER_EVIDENCE_TYPE * 0.5):
        type_potential = 0.7 # MEDIUM
    else:
        type_potential = 1.0 # HIGH

    # Artifact capacity check if project is specified
    artifact_potential = 1.0
    if project_id:
        # Check artifact diversity in this project
        # In a full implementation, we'd sum up contribution per artifact path
        # For NBA simplicity, if the project has > 5 artifacts of expected types, lower potential
        # (This is an approximation of the Phase 4 logic for artifact saturation)
        project_artifacts = db.query(Artifact).join(RepositorySnapshot).join(Project).filter(
            Project.id == project_id,
            Project.user_id == user_id
        ).all()
        
        # If the project already has an artifact named similarly to expected types (e.g. 'test_' for Testing)
        # we lower the potential. 
        # A simpler check: just look for the expected evidence types in this project.
        proj_evidence_count = 0
        for art in project_artifacts:
            for obs in art.observations:
                if obs.evidence and obs.evidence.type in action.expected_evidence_types:
                    proj_evidence_count += 1
                    
        if proj_evidence_count >= 2:
            artifact_potential = 0.3 # LOW
        elif proj_evidence_count == 1:
            artifact_potential = 0.7 # MEDIUM

    # The overall potential is the minimum of both headroom checks
    final_potential = min(type_potential, artifact_potential)
    return final_potential

def recalculate_next_best_action(user_id: int, db: Session) -> Optional[Recommendation]:
    # 1. Clear existing Recommendation
    db.query(Recommendation).filter(Recommendation.user_id == user_id).delete()
    
    # 2. Fetch Gaps
    gaps = db.query(Gap).filter(Gap.user_id == user_id).all()
    if not gaps:
        db.commit()
        return None
        
    # Map gaps by skill name for easy lookup
    gaps_by_skill_name = {}
    for gap in gaps:
        gaps_by_skill_name[gap.skill.name] = gap
        
    skill_map = get_skill_map_by_name(user_id, db)
    projects = db.query(Project).filter(Project.user_id == user_id).all()
    
    candidates: List[Candidate] = []
    
    # 3. Generate candidates
    catalog = get_action_catalog()
    for action in catalog:
        if action.skill_name not in gaps_by_skill_name:
            continue
            
        gap = gaps_by_skill_name[action.skill_name]
        actual_val = state_value(gap.actual_state)
        
        # Eligibility Rule 1: Current State
        if actual_val < state_value(action.min_current_state) or actual_val > state_value(action.max_current_state):
            continue
            
        # Eligibility Rule 3: Prerequisites
        prereqs_met = True
        for prereq_skill_name, required_state in action.prerequisites.items():
            user_prereq_skill = skill_map.get(prereq_skill_name)
            prereq_actual_state = user_prereq_skill.state if user_prereq_skill else SkillState.MISSING
            if state_value(prereq_actual_state) < state_value(required_state):
                prereqs_met = False
                break
                
        if not prereqs_met:
            continue
            
        # Effort multiplier
        effort_multiplier = 1.0 / (action.effort ** 0.5)
        
        # Eligibility Rule 4: Project Requirement
        if action.requires_existing_project:
            if not projects:
                continue
                
            for project in projects:
                # Rule 5: Action History Suppression
                if is_temporarily_suppressed(user_id, action.action_key, project.id, db):
                    continue
                    
                evidence_potential = calculate_evidence_potential(user_id, action, project.id, db)
                if evidence_potential <= 0.0:
                    continue
                    
                project_context_multiplier = 1.10
                priority_score = gap.severity * evidence_potential * effort_multiplier * project_context_multiplier
                
                candidates.append(Candidate(
                    action=action,
                    gap=gap,
                    project_id=project.id,
                    project_name=project.name,
                    evidence_potential=evidence_potential,
                    effort_multiplier=effort_multiplier,
                    project_context_multiplier=project_context_multiplier,
                    priority_score=priority_score
                ))
        else:
            # Rule 5: Action History Suppression
            if is_temporarily_suppressed(user_id, action.action_key, None, db):
                continue
                
            evidence_potential = calculate_evidence_potential(user_id, action, None, db)
            if evidence_potential <= 0.0:
                continue
                
            project_context_multiplier = 1.00
            priority_score = gap.severity * evidence_potential * effort_multiplier * project_context_multiplier
            
            candidates.append(Candidate(
                action=action,
                gap=gap,
                project_id=None,
                project_name=None,
                evidence_potential=evidence_potential,
                effort_multiplier=effort_multiplier,
                project_context_multiplier=project_context_multiplier,
                priority_score=priority_score
            ))

    if not candidates:
        db.commit()
        return None
        
    # Sort candidates
    # priority_score DESC, gap.severity DESC, evidence_potential DESC, effort_value ASC, project_id ASC, action_key ASC
    def sort_key(c: Candidate):
        # We negate descending ones to use python's default ASC sort
        return (
            -c.priority_score,
            -c.gap.severity,
            -c.evidence_potential,
            c.action.effort,
            c.project_id if c.project_id is not None else 0,
            c.action.action_key
        )
        
    candidates.sort(key=sort_key)
    
    best_candidate = candidates[0]
    
    title = best_candidate.action.title_template.replace("{project_name}", best_candidate.project_name or "")
    
    rec = Recommendation(
        user_id=user_id,
        gap_id=best_candidate.gap.id,
        action_key=best_candidate.action.action_key,
        project_id=best_candidate.project_id,
        title=title,
        description=best_candidate.action.description,
        effort=best_candidate.action.effort,
        priority_score=best_candidate.priority_score,
        calculation_version=NBA_CALCULATION_VERSION
    )
    
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec
