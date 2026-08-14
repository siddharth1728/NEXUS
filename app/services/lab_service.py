from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, Dict, Optional, Set
from collections import defaultdict

from app.models.project import (
    Project, RepositorySnapshot, Artifact, RawObservation,
    Evidence, EvidenceSkill, EvidenceType
)
from app.models.user import User, UserSkill, Gap, SkillState
from app.models.taxonomy import Skill
from app.config.concept_catalog import get_concept_catalog, get_concept, ConceptDefinition
from app.schemas.lab import (
    ConceptSummarySchema, ConceptDetailSchema, ProjectEvidenceReferenceSchema,
    DiagramStepSchema, TryItChallengeSchema, ChallengeOptionSchema,
    LabDiscoveryFeedResponse
)

def get_all_concepts(user_id: int, db: Session) -> List[ConceptSummarySchema]:
    catalog = get_concept_catalog()

    # 1. Fetch user skills & gaps
    user_skills = db.query(UserSkill).join(Skill).filter(UserSkill.user_id == user_id).all()
    user_skills_map = {us.skill.name: us.state for us in user_skills}

    user_gaps = db.query(Gap).join(Skill).filter(Gap.user_id == user_id).all()
    gap_skill_names = {g.skill.name for g in user_gaps}

    # 2. Fetch user project evidence grouped by skill and evidence type
    user_projects = db.query(Project).filter(Project.user_id == user_id).all()
    project_map = {p.id: p.name for p in user_projects}

    # Map project_id -> set of skill names and evidence types
    proj_evidence_types: Dict[int, Set[str]] = defaultdict(set)
    proj_skill_names: Dict[int, Set[str]] = defaultdict(set)

    if user_projects:
        proj_ids = [p.id for p in user_projects]
        ev_records = db.query(Evidence, RepositorySnapshot.project_id).join(
            RawObservation, Evidence.raw_observation_id == RawObservation.id
        ).join(
            Artifact, RawObservation.artifact_id == Artifact.id
        ).join(
            RepositorySnapshot, Artifact.snapshot_id == RepositorySnapshot.id
        ).filter(
            RepositorySnapshot.project_id.in_(proj_ids)
        ).all()

        for ev, p_id in ev_records:
            ev_type = ev.type.value if hasattr(ev.type, 'value') else str(ev.type)
            proj_evidence_types[p_id].add(ev_type)
            for es in ev.skills:
                if es.skill:
                    proj_skill_names[p_id].add(es.skill.name)

    summaries: List[ConceptSummarySchema] = []

    for key, c in catalog.items():
        # Find which projects exhibit this concept
        observed_projects = []
        for p_id, p_name in project_map.items():
            has_ev_type = any(et in proj_evidence_types[p_id] for et in c.related_evidence_types)
            has_skill = any(sn in proj_skill_names[p_id] for sn in c.related_skill_names)
            if has_ev_type or has_skill:
                observed_projects.append(p_name)

        # Determine user skill state for this concept
        matched_states = [user_skills_map[sn] for sn in c.related_skill_names if sn in user_skills_map]
        highest_state = matched_states[0] if matched_states else None
        if SkillState.STRONG in matched_states:
            highest_state = SkillState.STRONG
        elif SkillState.DEVELOPING in matched_states:
            highest_state = SkillState.DEVELOPING

        is_gap = any(sn in gap_skill_names for sn in c.related_skill_names)

        summaries.append(ConceptSummarySchema(
            concept_key=c.concept_key,
            title=c.title,
            short_description=c.short_description,
            domain=c.domain,
            difficulty=c.difficulty,
            related_skill_names=c.related_skill_names,
            user_skill_state=highest_state,
            observed_in_user_projects=sorted(observed_projects),
            is_gap_for_user=is_gap
        ))

    return summaries

def get_concept_detail(
    concept_key: str,
    user_id: int,
    db: Session,
    project_id: Optional[int] = None
) -> ConceptDetailSchema:
    c = get_concept(concept_key)
    if not c:
        raise HTTPException(status_code=404, detail="Engineering Lab concept not found")

    # Fetch user projects that demonstrate this concept
    user_projects = db.query(Project).filter(Project.user_id == user_id).all()
    proj_map = {p.id: p.name for p in user_projects}

    project_evidence_refs: List[ProjectEvidenceReferenceSchema] = []

    if user_projects:
        proj_ids = [p.id for p in user_projects]
        ev_query = db.query(
            Evidence, RawObservation, Artifact, RepositorySnapshot.project_id
        ).join(
            RawObservation, Evidence.raw_observation_id == RawObservation.id
        ).join(
            Artifact, RawObservation.artifact_id == Artifact.id
        ).join(
            RepositorySnapshot, Artifact.snapshot_id == RepositorySnapshot.id
        ).filter(
            RepositorySnapshot.project_id.in_(proj_ids)
        )

        ev_records = ev_query.all()

        # Group by project
        proj_matches: Dict[int, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0, "observations": [], "sources": []
        })

        for ev, obs, art, p_id in ev_records:
            ev_type = ev.type.value if hasattr(ev.type, 'value') else str(ev.type)
            ev_skill_names = [es.skill.name for es in ev.skills if es.skill]
            
            matches_type = ev_type in c.related_evidence_types
            matches_skill = any(sn in c.related_skill_names for sn in ev_skill_names)

            if matches_type or matches_skill:
                proj_matches[p_id]["count"] += 1
                if obs.observation_text and len(proj_matches[p_id]["observations"]) < 3:
                    proj_matches[p_id]["observations"].append(obs.observation_text)
                if art.file_path and len(proj_matches[p_id]["sources"]) < 3:
                    proj_matches[p_id]["sources"].append(art.file_path)

        for p_id, match_data in proj_matches.items():
            if match_data["count"] > 0:
                project_evidence_refs.append(ProjectEvidenceReferenceSchema(
                    project_id=p_id,
                    project_name=proj_map.get(p_id, f"Project #{p_id}"),
                    evidence_count=match_data["count"],
                    sample_observations=match_data["observations"],
                    sample_source_files=match_data["sources"]
                ))

    # Formulate "Why You Are Seeing This"
    if project_evidence_refs:
        names = ", ".join(r.project_name for r in project_evidence_refs)
        why_msg = f"You built code demonstrating this concept in {names}. NEXUS observed real engineering evidence in your repository."
    else:
        # Check gap
        user_gaps = db.query(Gap).join(Skill).filter(Gap.user_id == user_id).all()
        matching_gap = next((g for g in user_gaps if g.skill.name in c.related_skill_names), None)
        if matching_gap:
            why_msg = f"This concept directly addresses your destination signal requirement for {matching_gap.skill.name}."
        else:
            why_msg = "A foundational architectural concept relevant to your backend engineering journey."

    # Convert diagram steps & challenge to schemas
    diagram_steps = [
        DiagramStepSchema(
            step_number=s.step_number,
            label=s.label,
            technical_detail=s.technical_detail,
            layer=s.layer
        ) for s in c.diagram_steps
    ]

    challenge = TryItChallengeSchema(
        prompt=c.try_it_challenge.prompt,
        options=[
            ChallengeOptionSchema(
                text=opt.text,
                is_correct=opt.is_correct,
                explanation=opt.explanation
            ) for opt in c.try_it_challenge.options
        ],
        engineering_principle=c.try_it_challenge.engineering_principle
    )

    return ConceptDetailSchema(
        concept_key=c.concept_key,
        title=c.title,
        short_description=c.short_description,
        domain=c.domain,
        difficulty=c.difficulty,
        related_skill_names=c.related_skill_names,
        related_evidence_types=c.related_evidence_types,
        prerequisites=c.prerequisites,
        learning_objectives=c.learning_objectives,
        why_it_matters=c.why_it_matters,
        how_it_appears_in_projects=c.how_it_appears_in_projects,
        diagram_steps=diagram_steps,
        try_it_challenge=challenge,
        explain_it_prompt=c.explain_it_prompt,
        related_action_key=c.related_action_key,
        user_projects_using_this=project_evidence_refs,
        why_user_is_seeing_this=why_msg
    )

def get_lab_discovery_feed(user_id: int, db: Session) -> LabDiscoveryFeedResponse:
    summaries = get_all_concepts(user_id, db)
    
    # Priority 1: A concept demonstrated in the user's project
    demonstrated = [s for s in summaries if len(s.observed_in_user_projects) > 0]
    # Priority 2: A concept that is a gap
    gaps = [s for s in summaries if s.is_gap_for_user]

    if demonstrated:
        chosen_key = demonstrated[0].concept_key
        reason = f"Grounding discovery in your repository '{demonstrated[0].observed_in_user_projects[0]}'."
    elif gaps:
        chosen_key = gaps[0].concept_key
        reason = f"Addressing high-leverage destination gap for '{gaps[0].related_skill_names[0]}'."
    else:
        chosen_key = summaries[0].concept_key
        reason = "Foundational engineering discovery for backend architecture."

    featured_detail = get_concept_detail(chosen_key, user_id, db)

    return LabDiscoveryFeedResponse(
        featured_discovery=featured_detail,
        discovery_reason=reason,
        all_concepts=summaries
    )
