from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Dict, Optional, Set
from collections import defaultdict
from datetime import datetime

from app.models.project import (
    Project, RepositorySnapshot, Artifact, RawObservation,
    Evidence, EvidenceSkill, EvidenceType, SnapshotStatus
)
from app.models.user import User, UserSkill, Gap, SkillState
from app.models.profile import StudentProfile
from app.models.taxonomy import Skill, TargetRole, TargetRoleSkill
from app.schemas.project_intelligence import (
    ProjectIntelligenceResponse, ProjectMetadataInfo, ProjectEvidenceItem,
    ProjectEvidenceCategory, ProjectSignalItem, ProjectDimensionCoverage,
    ProjectGrowthOpportunity, ProjectEvolutionStep, ProjectGuidance
)
from app.services.nba_engine import generate_quest_candidates, get_latest_action_status
from app.config.action_catalog import get_action_catalog

def get_project_intelligence(db: Session, project_id: int, user_id: int) -> ProjectIntelligenceResponse:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or ownership mismatch")

    snapshots = db.query(RepositorySnapshot).filter(
        RepositorySnapshot.project_id == project.id
    ).order_by(RepositorySnapshot.captured_at.asc()).all()

    latest_snap = snapshots[-1] if snapshots else None

    # 1. Gather all artifacts & observations across snapshots
    all_artifacts = db.query(Artifact).join(RepositorySnapshot).filter(
        RepositorySnapshot.project_id == project.id
    ).all()
    
    all_observations = db.query(RawObservation).join(Artifact).join(RepositorySnapshot).filter(
        RepositorySnapshot.project_id == project.id
    ).all()

    # 2. Gather all evidence for this project
    all_evidence = db.query(Evidence).join(RawObservation).join(Artifact).join(RepositorySnapshot).filter(
        RepositorySnapshot.project_id == project.id
    ).all()

    # Detect languages and frameworks from artifacts & observations
    detected_languages = set()
    detected_frameworks = set()

    for a in all_artifacts:
        path = (a.file_path or '').lower()
        if path.endswith('.py'):
            detected_languages.add("Python")
        elif path.endswith('.js') or path.endswith('.ts'):
            detected_languages.add("JavaScript / TypeScript")
        elif path.endswith('.go'):
            detected_languages.add("Go")
        elif path.endswith('.rs'):
            detected_languages.add("Rust")
        elif path.endswith('.java'):
            detected_languages.add("Java")
            
        if "dockerfile" in path:
            detected_frameworks.add("Docker")
        if ".github/workflows" in path:
            detected_frameworks.add("GitHub Actions")
        if "alembic" in path:
            detected_frameworks.add("Alembic")
        if "pytest" in path or "conftest" in path or "test_" in path:
            detected_frameworks.add("pytest")

    for obs in all_observations:
        text = (obs.observation_text or '').lower()
        if "fastapi" in text:
            detected_frameworks.add("FastAPI")
        if "sqlalchemy" in text:
            detected_frameworks.add("SQLAlchemy")
        if "postgresql" in text:
            detected_frameworks.add("PostgreSQL")
        if "jwt" in text:
            detected_frameworks.add("JWT Auth")
        if "pytest" in text:
            detected_frameworks.add("pytest")

    # Fetch user profile to construct repo URL
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    gh_username = profile.github_username if profile else None
    repo_url = f"https://github.com/{gh_username}/{project.name}" if gh_username else None

    meta = ProjectMetadataInfo(
        project_id=project.id,
        name=project.name,
        github_repo_id=project.github_repo_id,
        repo_url=repo_url,
        default_branch=latest_snap.branch if latest_snap else None,
        latest_commit_sha=latest_snap.commit_sha if latest_snap else None,
        last_surveyed=latest_snap.captured_at if latest_snap else None,
        snapshot_status=latest_snap.status if latest_snap else "UNSURVEYED",
        artifact_count=len(all_artifacts),
        observation_count=len(all_observations),
        detected_languages=sorted(list(detected_languages)),
        detected_frameworks=sorted(list(detected_frameworks))
    )

    # 3. Group Evidence by Category
    evidence_by_type: Dict[str, List[ProjectEvidenceItem]] = defaultdict(list)
    ev_type_set = set()

    for ev in all_evidence:
        ev_type = ev.type.value if hasattr(ev.type, 'value') else str(ev.type)
        ev_type_set.add(ev_type)
        
        target_skills = [es.skill.name for es in ev.skills if es.skill]
        obs_text = ev.raw_observation.observation_text if ev.raw_observation else None

        evidence_by_type[ev_type].append(ProjectEvidenceItem(
            id=ev.id,
            type=ev_type,
            quality_score=ev.quality_score,
            freshness_weight=ev.freshness_weight,
            source_reference=ev.source_reference,
            raw_observation_text=obs_text,
            target_skills=target_skills
        ))

    evidence_categories = [
        ProjectEvidenceCategory(
            category_name=cat_name,
            evidence_count=len(items),
            items=items
        )
        for cat_name, items in sorted(evidence_by_type.items())
    ]

    # 4. Project Signal Map (What this project proves)
    user_skills = db.query(UserSkill).join(Skill).filter(UserSkill.user_id == user_id).all()
    user_skills_map = {us.skill.name: us for us in user_skills}

    skill_evidence_map: Dict[str, List[Evidence]] = defaultdict(list)
    for ev in all_evidence:
        for es in ev.skills:
            if es.skill:
                skill_evidence_map[es.skill.name].append(ev)

    signals: List[ProjectSignalItem] = []
    seen_skills = set()

    for skill_name, ev_list in skill_evidence_map.items():
        seen_skills.add(skill_name)
        us = user_skills_map.get(skill_name)
        current_state = us.state if us else SkillState.WEAK
        category = ev_list[0].skills[0].skill.category if (ev_list and ev_list[0].skills and ev_list[0].skills[0].skill) else "Backend"
        quality_avg = sum(e.quality_score for e in ev_list) / len(ev_list) if ev_list else 0.0

        signals.append(ProjectSignalItem(
            skill_name=skill_name,
            category=category,
            state=current_state,
            evidence_count=len(ev_list),
            quality_avg=round(quality_avg, 2),
            explanation=f"Evidence from this landmark contributes to your current {skill_name} capability."
        ))

    # Add destination role gaps as unexplored if missing in this project
    gaps = db.query(Gap).join(Skill).filter(Gap.user_id == user_id).all()
    for g in gaps:
        if g.skill.name not in seen_skills:
            signals.append(ProjectSignalItem(
                skill_name=g.skill.name,
                category=g.skill.category,
                state="UNEXPLORED",
                evidence_count=0,
                quality_avg=0.0,
                explanation=f"NEXUS has not observed evidence for {g.skill.name} in this repository."
            ))

    # 5. Factual Maturity Dimensions (No Fake Numbers!)
    dimensions: List[ProjectDimensionCoverage] = []

    def check_dimension(dim_key: str, display: str, req_types: List[str], expected_skills: List[str]):
        has_evidence = any(t in ev_type_set for t in req_types)
        if has_evidence:
            # Check highest state among matching skills
            states = [user_skills_map[s].state for s in expected_skills if s in user_skills_map]
            if SkillState.STRONG in states:
                status = "PROVEN"
            elif SkillState.DEVELOPING in states:
                status = "DEVELOPING"
            else:
                status = "DEVELOPING"
            notes = f"Observed {', '.join([t for t in req_types if t in ev_type_set])} artifacts."
        else:
            status = "NOT_OBSERVED"
            notes = "No matching artifacts or structural evidence detected."

        dimensions.append(ProjectDimensionCoverage(
            dimension_name=dim_key,
            display_name=display,
            status=status,
            evidence_notes=notes
        ))

    check_dimension("CORE_API", "API Design & Routing", ["API", "IMPLEMENTATION"], ["REST APIs", "Python"])
    check_dimension("DATABASE", "Database & Persistence", ["DATABASE"], ["PostgreSQL", "Database Design", "SQL"])
    check_dimension("AUTHENTICATION", "Authentication & Security", ["AUTHENTICATION"], ["Authentication"])
    check_dimension("TESTING", "Automated Testing", ["TESTING"], ["Testing"])
    check_dimension("DEPLOYMENT", "Containerization & Runtime", ["CONTAINERIZATION"], ["Docker"])
    check_dimension("CI_CD", "Continuous Integration", ["CI_CD"], ["CI/CD"])

    # Depth level calculation based on proven / developing dimensions
    active_dims = sum(1 for d in dimensions if d.status in ["PROVEN", "DEVELOPING"])
    if active_dims >= 4:
        depth_level = "BROAD_SIGNAL"
    elif active_dims >= 2:
        depth_level = "EXPANDING"
    elif active_dims >= 1:
        depth_level = "FOUNDATION"
    elif len(all_artifacts) > 0:
        depth_level = "BUILDING"
    else:
        depth_level = "UNSURVEYED"

    # 6. "Should You Improve This Project or Start New?" Guidance
    strong_dims = [d.display_name for d in dimensions if d.status == "PROVEN"]
    missing_dims = [d.display_name for d in dimensions if d.status == "NOT_OBSERVED"]

    if active_dims == 0:
        guidance = ProjectGuidance(
            recommendation="SURVEY_REQUIRED",
            headline="Execute First Survey",
            rationale="NEXUS requires an initial repository survey to evaluate engineering signals before recommending next steps.",
            strong_dimensions=[],
            missing_dimensions=missing_dims
        )
    elif active_dims >= 5:
        guidance = ProjectGuidance(
            recommendation="EXPAND_REPERTOIRE",
            headline="Comprehensive Landmark Established",
            rationale="This project demonstrates comprehensive engineering depth across API, database, testing, and infrastructure. Consider beginning a separate specialized architectural landmark (e.g. distributed systems, async workers, or microservices).",
            strong_dimensions=strong_dims,
            missing_dimensions=missing_dims
        )
    else:
        missing_names = ", ".join(missing_dims[:2]) if missing_dims else "additional coverage"
        guidance = ProjectGuidance(
            recommendation="IMPROVE_THIS_PROJECT",
            headline="Strengthen Existing Landmark",
            rationale=f"This repository already proves foundational architecture ({', '.join(strong_dims) if strong_dims else 'code structure'}). Adding {missing_names} here will create maximum evidence leverage.",
            strong_dimensions=strong_dims,
            missing_dimensions=missing_dims
        )

    # 7. What Could Grow Next (Proof Quests for this Project)
    growth_opps: List[ProjectGrowthOpportunity] = []
    candidates = generate_quest_candidates(user_id, db, ignore_suppression=True)
    matching_cands = [c for c in candidates if c.project_id == project.id or c.project_id is None]

    seen_action_keys = set()
    for c in matching_cands:
        if c.action.action_key in seen_action_keys:
            continue
        seen_action_keys.add(c.action.action_key)
        
        status = get_latest_action_status(user_id, c.action.action_key, project.id, db)
        why_p = f"Builds upon existing {c.action.expected_evidence_types[0].value} requirements in {project.name}."
        
        growth_opps.append(ProjectGrowthOpportunity(
            action_key=c.action.action_key,
            title=c.action.title_template.replace("{project_name}", project.name),
            skill_name=c.action.skill_name,
            mission_brief=c.action.mission_brief,
            why_this_project=why_p,
            verification_expectations=c.action.verification_expectations,
            status=status
        ))

    # 8. Project Evolution (Snapshot History)
    evolution: List[ProjectEvolutionStep] = []
    for idx, snap in enumerate(snapshots):
        snap_artifacts = db.query(Artifact).filter(Artifact.snapshot_id == snap.id).all()
        snap_obs = db.query(RawObservation).join(Artifact).filter(Artifact.snapshot_id == snap.id).all()
        snap_ev = db.query(Evidence).join(RawObservation).join(Artifact).filter(Artifact.snapshot_id == snap.id).all()
        
        ev_types = sorted(list(set(e.type.value if hasattr(e.type, 'value') else str(e.type) for e in snap_ev)))
        
        if ev_types:
            summary = f"Discovered {len(ev_types)} evidence categories: {', '.join(ev_types[:3])}."
        elif snap.status == SnapshotStatus.COMPLETED:
            summary = f"Survey completed. {len(snap_artifacts)} artifacts scanned."
        elif snap.status == SnapshotStatus.FAILED:
            summary = f"Survey failed: {snap.error_message or 'Analysis interrupted.'}"
        else:
            summary = "Survey initialized."

        evolution.append(ProjectEvolutionStep(
            survey_number=idx + 1,
            snapshot_id=snap.id,
            captured_at=snap.captured_at or datetime.utcnow(),
            commit_sha=snap.commit_sha,
            status=snap.status,
            artifact_count=len(snap_artifacts),
            observation_count=len(snap_obs),
            new_evidence_types=ev_types,
            summary=summary
        ))

    return ProjectIntelligenceResponse(
        metadata=meta,
        depth_level=depth_level,
        signals=signals,
        evidence_categories=evidence_categories,
        dimensions=dimensions,
        growth_opportunities=growth_opps,
        guidance=guidance,
        evolution=evolution
    )
