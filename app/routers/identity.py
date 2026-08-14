from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from collections import defaultdict
from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User, UserSkill, UserSkillHistory, SkillState
from app.models.project import Evidence, RawObservation, Artifact, RepositorySnapshot, Project, EvidenceSkill
from app.schemas.identity import (
    EngineeringIdentity, EngineeringJourney, AtlasTerritory, LandmarkNode, 
    SignalNode, UnexploredNode, EvidenceDetail, MeaningfulTransition, Discovery
)

router = APIRouter(prefix="/identity", tags=["Identity"])

@router.get("", response_model=EngineeringIdentity)
def get_identity(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Target Role
    profile = current_user.profile
    target_role_name = profile.target_role.name if profile and profile.target_role else None
    
    # 2. Get User Skills
    user_skills = db.query(UserSkill).filter(UserSkill.user_id == current_user.id).all()
    
    # Group skills into Unexplored and Proven
    # Unexplored = WEAK or MISSING
    # Proven = STRONG or DEVELOPING
    
    # category -> List[UnexploredNode]
    unexplored_by_category = defaultdict(list)
    # category -> project_id -> List[SignalNode]
    signals_by_category_and_project = defaultdict(lambda: defaultdict(list))
    # project lookup
    projects_lookup = {}
    
    proven_skill_ids = []
    
    for us in user_skills:
        cat = us.skill.category
        if us.state in [SkillState.STRONG, SkillState.DEVELOPING]:
            proven_skill_ids.append(us.skill.id)
            # Signals need evidence. We will fetch evidence below.
        else:
            unexplored_by_category[cat].append(UnexploredNode(
                skill_id=us.skill.id,
                skill_name=us.skill.name,
                category=cat
            ))
            
    # Fetch Evidence for Proven Skills
    if proven_skill_ids:
        # Join EvidenceSkill -> Evidence -> RawObs -> Artifact -> Snapshot -> Project
        rows = db.query(EvidenceSkill, Evidence, RawObservation, Artifact, RepositorySnapshot, Project)\
            .join(Evidence, EvidenceSkill.evidence_id == Evidence.id)\
            .join(RawObservation, Evidence.raw_observation_id == RawObservation.id)\
            .join(Artifact, RawObservation.artifact_id == Artifact.id)\
            .join(RepositorySnapshot, Artifact.snapshot_id == RepositorySnapshot.id)\
            .join(Project, RepositorySnapshot.project_id == Project.id)\
            .filter(EvidenceSkill.skill_id.in_(proven_skill_ids), Project.user_id == current_user.id).all()
            
        # skill_id -> project_id -> list of evidence details
        skill_project_evidence = defaultdict(lambda: defaultdict(list))
        
        for es, ev, ro, art, snap, proj in rows:
            projects_lookup[proj.id] = proj.name
            detail = EvidenceDetail(
                evidence_id=ev.id,
                type=ev.type.value,
                artifact_path=art.file_path,
                observation=ro.observation_text
            )
            skill_project_evidence[es.skill_id][proj.id].append(detail)
            
        # Reconstruct SignalNodes
        for us in user_skills:
            if us.skill.id in proven_skill_ids:
                cat = us.skill.category
                # For each project that has evidence for this skill
                for proj_id, ev_list in skill_project_evidence[us.skill.id].items():
                    signal = SignalNode(
                        skill_id=us.skill.id,
                        skill_name=us.skill.name,
                        state=us.state.value,
                        evidence=ev_list
                    )
                    signals_by_category_and_project[cat][proj_id].append(signal)

    # Build Atlas Territories
    all_categories = set(list(unexplored_by_category.keys()) + list(signals_by_category_and_project.keys()))
    atlas_territories = []
    
    for cat in all_categories:
        landmarks = []
        for proj_id, signals in signals_by_category_and_project[cat].items():
            landmarks.append(LandmarkNode(
                project_id=proj_id,
                project_name=projects_lookup.get(proj_id, "Unknown Project"),
                signals=signals
            ))
            
        atlas_territories.append(AtlasTerritory(
            category=cat,
            landmarks=landmarks,
            unexplored=unexplored_by_category[cat]
        ))

    # 3. Transitions & Discoveries from Latest Snapshot
    latest_snapshot = db.query(RepositorySnapshot).join(RepositorySnapshot.project).filter(
        RepositorySnapshot.project.has(user_id=current_user.id)
    ).order_by(desc(RepositorySnapshot.captured_at)).first()
    
    transitions = []
    discoveries = []
    
    if latest_snapshot:
        history_rows = db.query(UserSkillHistory).filter(
            UserSkillHistory.user_id == current_user.id,
            UserSkillHistory.snapshot_id == latest_snapshot.id
        ).order_by(desc(UserSkillHistory.changed_at)).all()
        
        for row in history_rows:
            transitions.append(MeaningfulTransition(
                skill_name=row.skill.name,
                previous_state=row.previous_state,
                new_state=row.new_state,
                changed_at=row.changed_at
            ))
            
        evidence_rows = db.query(Evidence).join(RawObservation).join(Artifact).filter(
            Artifact.snapshot_id == latest_snapshot.id
        ).order_by(desc(Evidence.quality_score)).limit(10).all()
        
        for e in evidence_rows:
            discoveries.append(Discovery(
                type=e.type.value,
                artifact_path=e.raw_observation.artifact.file_path,
                observation=e.raw_observation.observation_text
            ))

    journey = EngineeringJourney(
        meaningful_transitions=transitions,
        recent_discoveries=discoveries
    )

    github_username = profile.github_username if profile else None
    last_synced_dt = latest_snapshot.captured_at if latest_snapshot else None

    return EngineeringIdentity(
        target_role=target_role_name,
        github_username=github_username,
        last_synced=last_synced_dt,
        atlas_territories=atlas_territories,
        engineering_journey=journey
    )
