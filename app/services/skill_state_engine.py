from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import UserSkill, SkillState
from app.models.project import Evidence, EvidenceSkill, RawObservation, Artifact, RepositorySnapshot, Project
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

CALCULATION_VERSION = "skill_state_v1"
MAX_CONTRIBUTION_PER_EVIDENCE_TYPE = 1.5
MAX_CONTRIBUTION_PER_ARTIFACT = 2.0
MEANINGFUL_CONTRIBUTION_THRESHOLD = 0.5

def recalculate_user_skills(user_id: int, db: Session) -> None:
    """
    Idempotent function to recalculate the skill state for a user.
    Uses strict deterministic aggregation:
    1. contribution = quality_score * freshness_weight
    2. discard < 0.5 for meaningful checks
    3. group by EvidenceType and cap at 1.5
    4. group by Artifact and cap at 2.0
    5. evaluate thresholds (STRONG -> DEVELOPING -> WEAK -> MISSING)
    """
    # 1. Load all valid Evidence associated with the user's projects.
    evidence_skills = (
        db.query(EvidenceSkill)
        .join(Evidence, EvidenceSkill.evidence_id == Evidence.id)
        .join(RawObservation, Evidence.raw_observation_id == RawObservation.id)
        .join(Artifact, RawObservation.artifact_id == Artifact.id)
        .join(RepositorySnapshot, Artifact.snapshot_id == RepositorySnapshot.id)
        .join(Project, RepositorySnapshot.project_id == Project.id)
        .filter(Project.user_id == user_id)
        .all()
    )

    # 2. Group Evidence by Skill
    skills_evidence = defaultdict(list)
    for es in evidence_skills:
        skills_evidence[es.skill_id].append(es.evidence)

    # Fetch existing UserSkills to detect missing transitions
    existing_user_skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    existing_skill_ids = {us.skill_id for us in existing_user_skills}
    processed_skill_ids = set()

    # 3. Calculate evidence profile
    for skill_id, evidences in skills_evidence.items():
        processed_skill_ids.add(skill_id)
        
        # STEP 1: For every Evidence: contribution = quality_score * freshness_weight
        evidence_contributions = []
        for e in evidences:
            contribution = e.quality_score * e.freshness_weight
            evidence_contributions.append({
                "evidence": e,
                "contribution": contribution
            })
            
        # STEP 2: Discard contributions below 0.5 for meaningful evidence and diversity calculations.
        meaningful_list = [ec for ec in evidence_contributions if ec["contribution"] >= MEANINGFUL_CONTRIBUTION_THRESHOLD]
        meaningful_evidence_count = len(meaningful_list)
        unique_evidence_types = len({ec["evidence"].type for ec in meaningful_list})
        unique_artifacts = len({ec["evidence"].raw_observation.artifact_id for ec in meaningful_list})
        
        # STEP 3: Group meaningful evidence by EvidenceType. Sum its contributions. Cap that total at 1.5
        # Proportionally scale down the contributions if they exceed the cap.
        type_groups = defaultdict(list)
        for ec in meaningful_list:
            type_groups[ec["evidence"].type].append(ec)
            
        capped_evidence_contributions = []
        for e_type, ecs in type_groups.items():
            total_type_contrib = sum(ec["contribution"] for ec in ecs)
            scale = 1.0
            if total_type_contrib > MAX_CONTRIBUTION_PER_EVIDENCE_TYPE:
                scale = MAX_CONTRIBUTION_PER_EVIDENCE_TYPE / total_type_contrib
                
            for ec in ecs:
                capped_evidence_contributions.append({
                    "artifact_id": ec["evidence"].raw_observation.artifact_id,
                    "contribution": ec["contribution"] * scale
                })
                
        # STEP 4: Using the resulting per-evidence contributions, group by artifact_id. Cap at 2.0
        artifact_groups = defaultdict(list)
        for cec in capped_evidence_contributions:
            artifact_groups[cec["artifact_id"]].append(cec["contribution"])
            
        final_contribution = 0.0
        for a_id, contribs in artifact_groups.items():
            total_artifact_contrib = sum(contribs)
            final_contribution += min(total_artifact_contrib, MAX_CONTRIBUTION_PER_ARTIFACT)
            
        final_contribution = round(final_contribution, 4)
            
        # STEP 5: Classify State with strict precedence (STRONG -> DEVELOPING -> WEAK -> MISSING)
        state = SkillState.MISSING
        if final_contribution >= 3.0 and meaningful_evidence_count >= 4 and unique_evidence_types >= 2 and unique_artifacts >= 3:
            state = SkillState.STRONG
        elif final_contribution >= 1.5 and meaningful_evidence_count >= 2 and unique_evidence_types >= 1 and unique_artifacts >= 2:
            state = SkillState.DEVELOPING
        elif final_contribution >= 0.5 and meaningful_evidence_count >= 1 and unique_evidence_types >= 1 and unique_artifacts >= 1:
            state = SkillState.WEAK
            
        _upsert_user_skill(db, user_id, skill_id, state)
        
    # Transition missing skills (no valid evidence remaining)
    missing_skill_ids = existing_skill_ids - processed_skill_ids
    for skill_id in missing_skill_ids:
        _upsert_user_skill(db, user_id, skill_id, SkillState.MISSING)
        
    db.commit()

def _upsert_user_skill(db: Session, user_id: int, skill_id: int, state: SkillState):
    user_skill = db.query(UserSkill).filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id).first()
    if not user_skill:
        user_skill = UserSkill(user_id=user_id, skill_id=skill_id)
        db.add(user_skill)
        
    user_skill.state = state
    user_skill.calculated_at = func.now()
    user_skill.calculation_version = CALCULATION_VERSION
