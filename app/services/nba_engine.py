import math
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.user import Gap, UserSkill, SkillState, UserSkillHistory
from app.models.taxonomy import Skill
from app.models.project import Project, Evidence, Artifact, RawObservation, EvidenceType, RepositorySnapshot
from app.models.action import Recommendation, ActionHistory, ActionHistoryStatus
from app.config.action_catalog import get_action_catalog, ActionDefinition
from app.schemas.action import ProofQuestSummary, ProofQuestDetail, QuestVerificationResponse

MAX_CONTRIBUTION_PER_EVIDENCE_TYPE = 1.5
MAX_CONTRIBUTION_PER_ARTIFACT = 2.0
SUPPRESSION_DAYS = 30
NBA_CALCULATION_VERSION = "nba_v2_proof_quests"

def state_value(state_str: str) -> int:
    state_map = {
        SkillState.MISSING: 0,
        SkillState.WEAK: 1,
        SkillState.DEVELOPING: 2,
        SkillState.STRONG: 3,
    }
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

def get_latest_action_status(user_id: int, action_key: str, project_id: Optional[int], db: Session) -> str:
    """Determine the current lifecycle status for a quest."""
    query = db.query(ActionHistory).filter(
        ActionHistory.user_id == user_id,
        ActionHistory.action_key == action_key
    )
    if project_id is not None:
        query = query.filter(ActionHistory.project_id == project_id)
        
    latest = query.order_by(ActionHistory.created_at.desc()).first()
    if not latest:
        return "AVAILABLE"
    if latest.status == ActionHistoryStatus.STARTED:
        return "STARTED"
    if latest.status == ActionHistoryStatus.COMPLETED:
        return "COMPLETED"
    if latest.status == ActionHistoryStatus.DISMISSED:
        return "DISMISSED"
    return "AVAILABLE"

def calculate_evidence_potential(user_id: int, action: ActionDefinition, project_id: Optional[int], db: Session) -> float:
    """
    Evaluates Phase 4 anti-inflation rules.
    If the user has 1.5 contribution for the expected type -> LOW/NONE potential.
    HIGH=1.0, MEDIUM=0.7, LOW=0.3, NONE=0.0
    """
    if not action.expected_evidence_types:
        return 1.0

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
        return 0.0
        
    if total_type_contrib >= (MAX_CONTRIBUTION_PER_EVIDENCE_TYPE * 0.5):
        type_potential = 0.7
    else:
        type_potential = 1.0

    artifact_potential = 1.0
    if project_id:
        project_artifacts = db.query(Artifact).join(RepositorySnapshot).join(Project).filter(
            Project.id == project_id,
            Project.user_id == user_id
        ).all()
        
        proj_evidence_count = 0
        for art in project_artifacts:
            for obs in art.observations:
                if obs.evidence and obs.evidence.type in action.expected_evidence_types:
                    proj_evidence_count += 1
                    
        if proj_evidence_count >= 2:
            artifact_potential = 0.3
        elif proj_evidence_count == 1:
            artifact_potential = 0.7

    return min(type_potential, artifact_potential)

def generate_quest_candidates(user_id: int, db: Session, ignore_suppression: bool = False) -> List[Candidate]:
    """Generates and deterministically ranks all eligible Proof Quest candidates."""
    gaps = db.query(Gap).filter(Gap.user_id == user_id).all()
    if not gaps:
        return []
        
    gaps_by_skill_name = {gap.skill.name: gap for gap in gaps}
    skill_map = get_skill_map_by_name(user_id, db)
    projects = db.query(Project).filter(Project.user_id == user_id).all()
    
    candidates: List[Candidate] = []
    catalog = get_action_catalog()
    
    for action in catalog:
        if action.skill_name not in gaps_by_skill_name:
            continue
            
        gap = gaps_by_skill_name[action.skill_name]
        actual_val = state_value(gap.actual_state)
        
        # Rule 1: Current State bounds
        if actual_val < state_value(action.min_current_state) or actual_val > state_value(action.max_current_state):
            continue
            
        # Rule 2: Prerequisites
        prereqs_met = True
        for prereq_skill_name, required_state in action.prerequisites.items():
            user_prereq_skill = skill_map.get(prereq_skill_name)
            prereq_actual_state = user_prereq_skill.state if user_prereq_skill else SkillState.MISSING
            if state_value(prereq_actual_state) < state_value(required_state):
                prereqs_met = False
                break
                
        if not prereqs_met:
            continue
            
        effort_multiplier = 1.0 / (action.effort ** 0.5)
        
        if action.requires_existing_project:
            if not projects:
                continue
                
            for project in projects:
                if not ignore_suppression and is_temporarily_suppressed(user_id, action.action_key, project.id, db):
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
            if not ignore_suppression and is_temporarily_suppressed(user_id, action.action_key, None, db):
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

    def sort_key(c: Candidate):
        return (
            -c.priority_score,
            -c.gap.severity,
            -c.evidence_potential,
            c.action.effort,
            c.project_id if c.project_id is not None else 0,
            c.action.action_key
        )
        
    candidates.sort(key=sort_key)
    return candidates

def recalculate_next_best_action(user_id: int, db: Session) -> Optional[Recommendation]:
    db.query(Recommendation).filter(Recommendation.user_id == user_id).delete()
    
    candidates = generate_quest_candidates(user_id, db)
    if not candidates:
        db.commit()
        return None
        
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

def get_available_quests(user_id: int, db: Session) -> List[ProofQuestSummary]:
    """Returns the primary Proof Quest and secondary eligible quests."""
    candidates = generate_quest_candidates(user_id, db)
    if not candidates:
        return []

    summaries: List[ProofQuestSummary] = []
    seen_keys = set()

    for idx, c in enumerate(candidates):
        key = (c.action.action_key, c.project_id)
        if key in seen_keys:
            continue
        seen_keys.add(key)

        title = c.action.title_template.replace("{project_name}", c.project_name or "")
        status = get_latest_action_status(user_id, c.action.action_key, c.project_id, db)

        summaries.append(ProofQuestSummary(
            action_key=c.action.action_key,
            title=title,
            description=c.action.description,
            skill_name=c.action.skill_name,
            current_state=c.gap.actual_state,
            target_state=c.action.target_state,
            effort=c.action.effort,
            priority_score=c.priority_score,
            project_id=c.project_id,
            project_name=c.project_name,
            is_primary=(idx == 0),
            status=status
        ))

    return summaries

def get_quest_detail(user_id: int, action_key: str, db: Session, project_id: Optional[int] = None) -> Optional[ProofQuestDetail]:
    """Reconstructs the full Proof Quest mission dossier."""
    catalog = get_action_catalog()
    action = next((a for a in catalog if a.action_key == action_key), None)
    if not action:
        return None

    # Find Gap or UserSkill
    gap = db.query(Gap).join(Skill).filter(Gap.user_id == user_id, Skill.name == action.skill_name).first()
    current_state = gap.actual_state if gap else SkillState.MISSING
    
    # Ownership check if project_id is given
    project = None
    if project_id is not None:
        project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    elif action.requires_existing_project:
        # Pick candidate project for user
        candidates = generate_quest_candidates(user_id, db, ignore_suppression=True)
        matching = [c for c in candidates if c.action.action_key == action_key and c.project_id is not None]
        if matching:
            project_id = matching[0].project_id
            project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()

    project_name = project.name if project else None
    title = action.title_template.replace("{project_name}", project_name or "")
    
    why_proj = f"This repository demonstrates base engineering patterns but lacks sufficient {action.expected_evidence_types[0].value} proof." if project else None
    why_quest = f"Resolves your {gap.severity if gap else 1.0} severity gap in {action.skill_name}."

    status = get_latest_action_status(user_id, action_key, project.id if project else None, db)

    return ProofQuestDetail(
        action_key=action.action_key,
        title=title,
        description=action.description,
        mission_brief=action.mission_brief,
        skill_name=action.skill_name,
        current_state=current_state,
        target_state=action.target_state,
        effort=action.effort,
        priority_score=gap.severity if gap else 1.0,
        expected_evidence_types=[t.value for t in action.expected_evidence_types],
        expected_artifact_types=action.expected_artifact_types,
        verification_expectations=action.verification_expectations,
        project_id=project.id if project else None,
        project_name=project_name,
        why_this_project=why_proj,
        why_this_quest=why_quest,
        status=status
    )

def verify_quest_outcome(user_id: int, action_key: str, db: Session) -> QuestVerificationResponse:
    """Inspects whether repository sync created verified evidence for this quest."""
    catalog = get_action_catalog()
    action = next((a for a in catalog if a.action_key == action_key), None)
    if not action:
        return QuestVerificationResponse(
            action_key=action_key,
            skill_name="Unknown",
            verified=False,
            current_state=SkillState.MISSING,
            new_evidence_count=0,
            what_nexus_found=[],
            what_is_missing=["Unknown action key"],
            explanation="Invalid Proof Quest key."
        )

    # Fetch UserSkill
    user_skill = db.query(UserSkill).join(Skill).filter(
        UserSkill.user_id == user_id,
        Skill.name == action.skill_name
    ).first()
    
    current_state = user_skill.state if user_skill else SkillState.MISSING

    # Fetch previous state from history
    history = db.query(UserSkillHistory).join(Skill).filter(
        UserSkillHistory.user_id == user_id,
        Skill.name == action.skill_name
    ).order_by(UserSkillHistory.changed_at.desc()).first()
    
    prev_state = history.previous_state if history else None

    # Fetch evidence for this skill
    user_evidence = db.query(Evidence).join(RawObservation).join(Artifact).join(RepositorySnapshot).join(Project).filter(
        Project.user_id == user_id
    ).all()

    matching_evidence = [e for e in user_evidence if e.type in action.expected_evidence_types]
    found_observations = [e.raw_observation_text for e in matching_evidence if e.raw_observation_text]

    verified = state_value(current_state) >= state_value(action.target_state)

    missing = []
    if not verified:
        for t in action.expected_evidence_types:
            if not any(e.type == t for e in matching_evidence):
                missing.append(f"Verifiable {t.value} artifacts matching taxonomy rules.")
        if not missing:
            missing.append("Additional evidence diversity or quality score required to cross state threshold.")

    explanation = (
        f"Verification complete: New evidence confirmed. {action.skill_name} state advanced to {current_state}."
        if verified else
        f"Not yet verified: NEXUS analyzed latest repositories but {action.skill_name} requires more evidence to advance to {action.target_state}."
    )

    # Next quest
    recalc = recalculate_next_best_action(user_id, db)
    next_key = recalc.action_key if recalc else None

    return QuestVerificationResponse(
        action_key=action_key,
        skill_name=action.skill_name,
        verified=verified,
        current_state=current_state,
        previous_state=prev_state,
        new_evidence_count=len(matching_evidence),
        what_nexus_found=found_observations[:5],
        what_is_missing=missing,
        explanation=explanation,
        next_recommended_action_key=next_key
    )
