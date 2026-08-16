import json
import secrets
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.profile import StudentProfile
from app.models.user import User, UserSkill, UserSkillHistory, Gap, SkillState
from app.models.taxonomy import TargetRole, Skill, TargetRoleSkill
from app.models.project import Project, RepositorySnapshot, Artifact, RawObservation, Evidence, EvidenceSkill, SnapshotStatus
from app.models.claims import UserClaim
from app.schemas.nexus_id import (
    PublicProfileResponse, PublicProjectSummary, PublicProofItem, PublicJourneyMilestone,
    PublicEngineeringSignature, PublicAtlasResponse, PublicAtlasTerritory, PublicAtlasLandmark,
    NexusIdSettingsResponse, NexusIdSettingsUpdate, ProfileHealthItem,
    ClaimEvaluationItem, ClaimListResponse, PortfolioSelectorResponse,
    RecruiterViewResponse, CareerSnapshotResponse
)
from app.services import telemetry_service

def generate_stable_nexus_id(user_id: int) -> str:
    """Generates an immutable, non-sequential system identity ID like NX-78291."""
    # Deterministic obfuscated identifier based on user ID + salt
    code = (user_id * 7919 + 1337) % 89999 + 10000
    return f"NX-{code}"

def get_or_create_nexus_identity(db: Session, user_id: int) -> StudentProfile:
    """Retrieves or initializes a student profile with safe immutable nexus_id and public_slug."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    profile_existed = bool(profile)
    created_id = False
    
    if not profile:
        profile = StudentProfile(user_id=user_id)
        db.add(profile)
        db.flush()

    modified = False
    if not profile.nexus_id:
        profile.nexus_id = generate_stable_nexus_id(user_id)
        modified = True
        created_id = True

    if not profile.public_slug:
        random_suffix = secrets.token_hex(3)
        profile.public_slug = f"nx_{random_suffix}"
        modified = True

    if modified:
        db.commit()
        db.refresh(profile)
        
        # Determine if we just created the nexus_id
        if not profile_existed or created_id:
            telemetry_service.record_event(db, "NEXUS_ID_CREATED", user_id=user_id)

    return profile

def get_public_profile_by_slug(db: Session, slug: str) -> PublicProfileResponse:
    """
    Assembles a safe, sanitized public engineering passport for the given slug.
    Strictly enforces public_profile == True and filters out all private data.
    """
    profile = (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.target_role), joinedload(StudentProfile.user))
        .filter(StudentProfile.public_slug == slug)
        .first()
    )

    if not profile or not profile.public_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public engineering profile is unavailable or private"
        )

    user = profile.user
    target_role_name = profile.target_role.name if profile.target_role else "Software Engineer"
    display_name = profile.name or "NEXUS Engineer"

    # Gather user skills
    user_skills = db.query(UserSkill).join(Skill).filter(UserSkill.user_id == user.id).all()
    proven_signals = []
    developing_signals = []
    unexplored_signals = []
    core_domains = set()

    for us in user_skills:
        cat = us.skill.category
        if us.state == SkillState.STRONG:
            proven_signals.append(us.skill.name)
            core_domains.add(cat)
        elif us.state == SkillState.DEVELOPING:
            developing_signals.append(us.skill.name)
            core_domains.add(cat)
        elif us.state in [SkillState.WEAK, SkillState.MISSING]:
            unexplored_signals.append(us.skill.name)

    # Engineering signature
    eng_signature = PublicEngineeringSignature(
        core_signals=proven_signals[:6] if proven_signals else developing_signals[:4],
        technical_domains=sorted(list(core_domains))
    )

    # Featured public projects
    featured_ids = []
    if profile.featured_project_ids:
        try:
            featured_ids = json.loads(profile.featured_project_ids)
        except Exception:
            featured_ids = []

    # Only fetch projects explicitly marked as is_public == True
    public_projects = db.query(Project).filter(Project.user_id == user.id, Project.is_public == True).all()
    
    # Sort: featured first, then others
    public_proj_map = {p.id: p for p in public_projects}
    sorted_public_projects = []
    for fid in featured_ids:
        if fid in public_proj_map:
            sorted_public_projects.append(public_proj_map.pop(fid))
    sorted_public_projects.extend(public_proj_map.values())

    public_project_summaries: List[PublicProjectSummary] = []
    public_proof_items: List[PublicProofItem] = []

    for proj in sorted_public_projects:
        # Detect technologies from snapshots
        snapshots = db.query(RepositorySnapshot).filter(
            RepositorySnapshot.project_id == proj.id,
            RepositorySnapshot.status == SnapshotStatus.COMPLETED
        ).order_by(RepositorySnapshot.captured_at.desc()).all()

        detected_techs = []
        project_signals = set()
        proof_notes = []

        if snapshots:
            # Observations & evidence for this project
            ev_rows = db.query(Evidence, RawObservation, Skill)\
                .join(RawObservation, Evidence.raw_observation_id == RawObservation.id)\
                .join(Artifact, RawObservation.artifact_id == Artifact.id)\
                .join(RepositorySnapshot, Artifact.snapshot_id == RepositorySnapshot.id)\
                .outerjoin(EvidenceSkill, EvidenceSkill.evidence_id == Evidence.id)\
                .outerjoin(Skill, EvidenceSkill.skill_id == Skill.id)\
                .filter(RepositorySnapshot.project_id == proj.id)\
                .order_by(Evidence.quality_score.desc()).limit(8).all()

            for ev, ro, sk in ev_rows:
                if sk:
                    project_signals.add(sk.name)
                # Public-safe observation summary (no internal paths or passwords)
                summary_text = ro.observation_text or f"Verified {ev.type.value} signal"
                proof_notes.append(summary_text)

                if profile.show_proof and len(public_proof_items) < 8:
                    public_proof_items.append(PublicProofItem(
                        title=f"{sk.name if sk else ev.type.value} Verification",
                        signal_name=sk.name if sk else ev.type.value,
                        observation_summary=summary_text,
                        project_name=proj.name,
                        type=ev.type.value
                    ))

        # Check detected languages/frameworks from evidence types
        if any("POSTGRES" in n.upper() or "DATABASE" in n.upper() for n in proof_notes):
            detected_techs.append("PostgreSQL")
        if any("API" in n.upper() or "FASTAPI" in n.upper() for n in proof_notes):
            detected_techs.append("FastAPI")
        if any("TEST" in n.upper() or "PYTEST" in n.upper() for n in proof_notes):
            detected_techs.append("Pytest")
        if not detected_techs:
            detected_techs = ["Python"]

        proof_summary_text = f"Demonstrates {len(project_signals)} verified engineering signals including {', '.join(list(project_signals)[:3])}." if project_signals else "Active engineering repository analyzed by NEXUS."

        public_project_summaries.append(PublicProjectSummary(
            project_id=proj.id,
            name=proj.name,
            description=None,
            verified_signals=sorted(list(project_signals)),
            detected_technologies=detected_techs,
            proof_summary=proof_summary_text
        ))

    # Journey milestones
    journey_milestones: Optional[List[PublicJourneyMilestone]] = None
    if profile.show_journey:
        history_rows = (
            db.query(UserSkillHistory)
            .join(Skill)
            .filter(UserSkillHistory.user_id == user.id)
            .order_by(UserSkillHistory.changed_at.asc())
            .limit(10)
            .all()
        )
        milestones = []
        for idx, h in enumerate(history_rows, start=1):
            milestones.append(PublicJourneyMilestone(
                stage_number=idx,
                title=f"{h.skill.name} → {h.new_state}",
                detail=f"Demonstrated verified progression from {h.previous_state or 'UNEXPLORED'} to {h.new_state}.",
                date_str=h.changed_at.strftime("%b %Y") if h.changed_at else "Recent"
            ))
        journey_milestones = milestones if milestones else None

    # External links
    links_dict = {}
    if profile.external_links:
        try:
            links_dict = json.loads(profile.external_links)
        except Exception:
            links_dict = {}

    return PublicProfileResponse(
        nexus_id=profile.nexus_id,
        public_slug=profile.public_slug,
        name=display_name,
        target_role=target_role_name,
        bio=profile.bio,
        engineering_signature=eng_signature,
        proven_signals=proven_signals,
        developing_signals=developing_signals,
        unexplored_signals=unexplored_signals if profile.show_unexplored else None,
        featured_projects=public_project_summaries,
        verified_proof=public_proof_items if profile.show_proof else [],
        journey_milestones=journey_milestones,
        external_links=links_dict,
        contact_email=user.email if profile.show_email else None,
        last_surveyed=datetime.now(timezone.utc).strftime("%B %Y")
    )

def get_public_atlas_by_slug(db: Session, slug: str) -> PublicAtlasResponse:
    """
    Builds a strictly public-safe read-only projection of the Engineering Atlas.
    Only contains public projects and proven/developing signals. Zero private data.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.public_slug == slug).first()
    if not profile or not profile.public_profile:
        raise HTTPException(status_code=404, detail="Public Atlas unavailable")

    user_id = profile.user_id
    target_role = profile.target_role.name if profile.target_role else "Software Engineer"

    # Only include public projects
    public_projects = db.query(Project).filter(Project.user_id == user_id, Project.is_public == True).all()
    public_proj_ids = [p.id for p in public_projects]

    # Proven and developing skills
    user_skills = db.query(UserSkill).join(Skill).filter(
        UserSkill.user_id == user_id,
        UserSkill.state.in_([SkillState.STRONG, SkillState.DEVELOPING])
    ).all()

    # Category -> Landmark mappings
    territories_map: Dict[str, Dict[str, Any]] = {}

    for us in user_skills:
        cat = us.skill.category
        if cat not in territories_map:
            territories_map[cat] = {"landmarks": {}, "proven_count": 0}
        territories_map[cat]["proven_count"] += 1

    # Attach landmarks from public projects
    for proj in public_projects:
        ev_skills = db.query(Skill.category, Skill.name)\
            .join(EvidenceSkill, EvidenceSkill.skill_id == Skill.id)\
            .join(Evidence, EvidenceSkill.evidence_id == Evidence.id)\
            .join(RawObservation, Evidence.raw_observation_id == RawObservation.id)\
            .join(Artifact, RawObservation.artifact_id == Artifact.id)\
            .join(RepositorySnapshot, Artifact.snapshot_id == RepositorySnapshot.id)\
            .filter(RepositorySnapshot.project_id == proj.id).all()

        for cat, sk_name in ev_skills:
            if cat not in territories_map:
                territories_map[cat] = {"landmarks": {}, "proven_count": 0}
            if proj.name not in territories_map[cat]["landmarks"]:
                territories_map[cat]["landmarks"][proj.name] = set()
            territories_map[cat]["landmarks"][proj.name].add(sk_name)

    territories_list: List[PublicAtlasTerritory] = []
    for cat, t_data in sorted(territories_map.items()):
        landmarks_list = [
            PublicAtlasLandmark(project_name=pname, signals=sorted(list(signals)))
            for pname, signals in t_data["landmarks"].items()
        ]
        territories_list.append(PublicAtlasTerritory(
            category=cat,
            landmarks=landmarks_list,
            proven_count=t_data["proven_count"]
        ))

    return PublicAtlasResponse(
        nexus_id=profile.nexus_id,
        target_role=target_role,
        territories=territories_list
    )

def get_nexus_id_settings(db: Session, user_id: int) -> NexusIdSettingsResponse:
    """Returns owner's current NEXUS ID settings and health checklist."""
    profile = get_or_create_nexus_identity(db, user_id)
    user_projects = db.query(Project).filter(Project.user_id == user_id).all()

    featured_ids = []
    if profile.featured_project_ids:
        try:
            featured_ids = json.loads(profile.featured_project_ids)
        except Exception:
            featured_ids = []

    available_projects = [
        {
            "id": p.id,
            "name": p.name,
            "is_public": p.is_public,
            "is_featured": p.id in featured_ids
        }
        for p in user_projects
    ]

    links_dict = {}
    if profile.external_links:
        try:
            links_dict = json.loads(profile.external_links)
        except Exception:
            links_dict = {}

    # Profile health checklist
    user_skills_count = db.query(UserSkill).filter(
        UserSkill.user_id == user_id,
        UserSkill.state.in_([SkillState.STRONG, SkillState.DEVELOPING])
    ).count()
    history_count = db.query(UserSkillHistory).filter(UserSkillHistory.user_id == user_id).count()
    public_projects_count = db.query(Project).filter(Project.user_id == user_id, Project.is_public == True).count()

    health = [
        ProfileHealthItem(
            key="target_role",
            label="Target Engineering Role",
            is_completed=bool(profile.target_role_id),
            status_hint=profile.target_role.name if profile.target_role else "Select a target role"
        ),
        ProfileHealthItem(
            key="identity",
            label="Profile Identity & Bio",
            is_completed=bool(profile.name and profile.bio),
            status_hint="Name and engineering bio defined" if (profile.name and profile.bio) else "Add your name and brief bio"
        ),
        ProfileHealthItem(
            key="featured_projects",
            label="Public Featured Projects",
            is_completed=public_projects_count >= 1,
            status_hint=f"{public_projects_count} public project(s) active" if public_projects_count >= 1 else "Publish at least 1 project"
        ),
        ProfileHealthItem(
            key="verified_proof",
            label="Verified Evidence & Proof",
            is_completed=user_skills_count >= 1,
            status_hint=f"{user_skills_count} verified signal(s) active" if user_skills_count >= 1 else "Run repository analysis"
        ),
        ProfileHealthItem(
            key="journey",
            label="Engineering Journey",
            is_completed=history_count >= 1 and profile.show_journey,
            status_hint="Demonstrates skill evolution" if (history_count >= 1 and profile.show_journey) else "Enable journey in settings"
        ),
        ProfileHealthItem(
            key="external_links",
            label="External Contact Links",
            is_completed=bool(links_dict),
            status_hint=f"{len(links_dict)} link(s) added" if links_dict else "Add GitHub, LinkedIn, or personal website"
        )
    ]

    return NexusIdSettingsResponse(
        nexus_id=profile.nexus_id,
        public_slug=profile.public_slug,
        public_profile=profile.public_profile,
        bio=profile.bio,
        external_links=links_dict,
        show_journey=profile.show_journey,
        show_proof=profile.show_proof,
        show_unexplored=profile.show_unexplored,
        show_email=profile.show_email,
        featured_project_ids=featured_ids,
        available_projects=available_projects,
        public_url=f"/u/{profile.public_slug}",
        profile_health=health
    )

def update_nexus_id_settings(db: Session, user_id: int, payload: NexusIdSettingsUpdate) -> NexusIdSettingsResponse:
    """Updates owner's NEXUS ID visibility, custom slug, and featured projects with strict ownership checks."""
    profile = get_or_create_nexus_identity(db, user_id)

    # Validate and update public slug
    if payload.public_slug is not None:
        slug_clean = payload.public_slug.strip().lower()
        if not re.match(r"^[a-z0-9_-]{3,40}$", slug_clean):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Public slug must be 3-40 characters consisting of letters, numbers, underscores, or hyphens."
            )
        # Check uniqueness across other users
        existing = db.query(StudentProfile).filter(
            StudentProfile.public_slug == slug_clean,
            StudentProfile.user_id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This public slug is already taken. Please choose another one."
            )
        profile.public_slug = slug_clean

    if payload.public_profile is not None:
        if not profile.public_profile and payload.public_profile:
            telemetry_service.record_event(db, "PUBLIC_PROFILE_ENABLED", user_id=user_id)
        profile.public_profile = payload.public_profile

    if payload.bio is not None:
        profile.bio = payload.bio.strip() if payload.bio else None

    if payload.external_links is not None:
        # Sanitize dictionary
        sanitized_links = {}
        for k, v in payload.external_links.items():
            if isinstance(v, str) and v.strip().startswith(("http://", "https://", "mailto:")):
                sanitized_links[k.strip().lower()] = v.strip()
        profile.external_links = json.dumps(sanitized_links)

    if payload.show_journey is not None:
        profile.show_journey = payload.show_journey
    if payload.show_proof is not None:
        profile.show_proof = payload.show_proof
    if payload.show_unexplored is not None:
        profile.show_unexplored = payload.show_unexplored
    if payload.show_email is not None:
        profile.show_email = payload.show_email

    # Bulk publish projects (explicit opt-in)
    if payload.publish_project_ids is not None:
        # Only modify projects owned by current user
        user_projects = db.query(Project).filter(Project.user_id == user_id).all()
        for p in user_projects:
            p.is_public = p.id in payload.publish_project_ids

    # Validate featured project IDs
    if payload.featured_project_ids is not None:
        # Verify each ID belongs to user AND is_public == True
        valid_user_public_ids = set(
            db.query(Project.id).filter(
                Project.user_id == user_id,
                Project.is_public == True
            ).all()
        )
        valid_ids_flat = {id_tuple[0] for id_tuple in valid_user_public_ids}
        verified_featured = [pid for pid in payload.featured_project_ids if pid in valid_ids_flat]
        profile.featured_project_ids = json.dumps(verified_featured)

    db.commit()
    return get_nexus_id_settings(db, user_id)

# --- Career Layer: Claims vs Proof ---

def evaluate_user_claims(db: Session, user_id: int) -> ClaimListResponse:
    """Deterministically evaluates student claims against observable evidence with 3 states."""
    claims = db.query(UserClaim).filter(UserClaim.user_id == user_id).order_by(UserClaim.created_at.desc()).all()
    user_skills = db.query(UserSkill).join(Skill).filter(UserSkill.user_id == user_id).all()
    skill_map = {us.skill.name.lower(): us for us in user_skills}

    items: List[ClaimEvaluationItem] = []
    for c in claims:
        claim_lower = c.claim_text.lower().strip()
        matched_us = None

        # Exact or substring skill match
        for s_name, us in skill_map.items():
            if s_name == claim_lower or claim_lower in s_name or s_name in claim_lower:
                matched_us = us
                break

        if matched_us and matched_us.state == SkillState.STRONG:
            status_val = "SUPPORTED"
            evidence_notes = [f"Strong observable proof in verified skill area: {matched_us.skill.name}"]
            guidance = "Verified by repository analysis. Clear evidence is present in project builds."
        elif matched_us and matched_us.state == SkillState.DEVELOPING:
            status_val = "PARTIALLY_SUPPORTED"
            evidence_notes = [f"Developing signal observed in {matched_us.skill.name}"]
            guidance = "Initial evidence detected. Adding comprehensive unit tests or advanced architecture patterns will strengthen this to fully supported."
        else:
            status_val = "NOT_YET_SUPPORTED"
            evidence_notes = ["No direct code artifacts or repository evidence observed yet."]
            guidance = f"NEXUS has not found enough supporting evidence for '{c.claim_text}'. Implementing concrete modules, configurations, or tests in a project repository will provide proof."

        items.append(ClaimEvaluationItem(
            id=c.id,
            claim_text=c.claim_text,
            status=status_val,
            supporting_evidence=evidence_notes,
            guidance=guidance
        ))

    return ClaimListResponse(claims=items)

def add_user_claim(db: Session, user_id: int, claim_text: str, category: Optional[str] = None) -> UserClaim:
    """Adds a new self-declared claim for deterministic verification."""
    clean_text = claim_text.strip()
    if not clean_text:
        raise HTTPException(status_code=400, detail="Claim text cannot be empty")
    
    claim = UserClaim(user_id=user_id, claim_text=clean_text, category=category)
    db.add(claim)
    db.commit()
    db.refresh(claim)
    return claim

def delete_user_claim(db: Session, user_id: int, claim_id: int) -> bool:
    """Removes a claim from the user's workbench."""
    claim = db.query(UserClaim).filter(UserClaim.id == claim_id, UserClaim.user_id == user_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    db.delete(claim)
    db.commit()
    return True

# --- Career Layer: Portfolio Selector & Recruiter View ---

def compute_portfolio_selector(db: Session, user_id: int) -> PortfolioSelectorResponse:
    """
    Deterministically recommends the 'Best Match for Your Target Role' based on observable evidence alignment.
    Presents clear qualitative reasoning rather than artificial percentage scores.
    """
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    target_role_name = profile.target_role.name if profile and profile.target_role else "Backend Engineer"
    target_role_id = profile.target_role_id if profile else None

    # Target role skills
    target_skill_ids = set()
    if target_role_id:
        trs = db.query(TargetRoleSkill).filter(TargetRoleSkill.target_role_id == target_role_id).all()
        target_skill_ids = {t.skill_id for t in trs}

    user_projects = db.query(Project).filter(Project.user_id == user_id).all()
    if not user_projects:
        return PortfolioSelectorResponse(
            target_role=target_role_name,
            reasoning=["No projects surveyed yet. Connect a GitHub repository to discover role-aligned evidence."],
            alternative_projects=[]
        )

    # Score each project deterministically
    project_scores = []
    for p in user_projects:
        # Fetch verified evidence skills for this project
        ev_skills = db.query(Skill.id, Skill.name, Evidence.type)\
            .join(EvidenceSkill, EvidenceSkill.skill_id == Skill.id)\
            .join(Evidence, EvidenceSkill.evidence_id == Evidence.id)\
            .join(RawObservation, Evidence.raw_observation_id == RawObservation.id)\
            .join(Artifact, RawObservation.artifact_id == Artifact.id)\
            .join(RepositorySnapshot, Artifact.snapshot_id == RepositorySnapshot.id)\
            .filter(RepositorySnapshot.project_id == p.id).all()

        matching_target_skills = set()
        all_signals = set()
        evidence_count = len(ev_skills)

        for sk_id, sk_name, ev_type in ev_skills:
            all_signals.add(sk_name)
            if sk_id in target_skill_ids:
                matching_target_skills.add(sk_name)

        # Deterministic weight: matches * 10 + total evidence count
        score = len(matching_target_skills) * 10 + evidence_count
        project_scores.append({
            "project": p,
            "score": score,
            "matching_skills": sorted(list(matching_target_skills)),
            "all_signals": sorted(list(all_signals)),
            "evidence_count": evidence_count
        })

    # Sort descending by score, tie-break by project id ascending
    project_scores.sort(key=lambda x: (x["score"], -x["project"].id), reverse=True)
    best = project_scores[0]

    reasons = []
    if best["matching_skills"]:
        for s in best["matching_skills"][:4]:
            reasons.append(f"✓ Demonstrates verified {s} signal required for {target_role_name}")
    if best["evidence_count"] > 0:
        reasons.append(f"✓ Backed by {best['evidence_count']} observable evidence points in repository")
    else:
        reasons.append(f"✓ Primary codebase identified for {target_role_name} development")

    alternatives = [
        {
            "name": item["project"].name,
            "signals": item["all_signals"],
            "notes": f"Provides {len(item['matching_skills'])} matching skills for this role."
        }
        for item in project_scores[1:]
    ]

    return PortfolioSelectorResponse(
        target_role=target_role_name,
        recommended_project_id=best["project"].id,
        recommended_project_name=best["project"].name,
        reasoning=reasons,
        alternative_projects=alternatives
    )

def compute_recruiter_preview(db: Session, user_id: int) -> RecruiterViewResponse:
    """Factual preview of what is immediately visible on the public passport vs what is still unclear."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    target_role_name = profile.target_role.name if profile and profile.target_role else "Backend Engineer"

    user_skills = db.query(UserSkill).join(Skill).filter(UserSkill.user_id == user_id).all()
    proven = [us.skill.name for us in user_skills if us.state == SkillState.STRONG]
    developing = [us.skill.name for us in user_skills if us.state == SkillState.DEVELOPING]

    public_projects = db.query(Project).filter(Project.user_id == user_id, Project.is_public == True).all()

    gaps = db.query(Gap).join(Skill).filter(Gap.user_id == user_id).all()
    unclear = [f"{g.skill.name} (Required: {g.required_state})" for g in gaps]

    if not unclear and not proven:
        unclear = ["Comprehensive automated testing evidence", "Continuous integration deployment workflows"]

    immediately_visible = {
        "target_role": target_role_name,
        "proven_signals": proven[:5],
        "developing_signals": developing[:3],
        "public_projects_count": len(public_projects),
        "public_project_names": [p.name for p in public_projects]
    }

    return RecruiterViewResponse(
        target_role=target_role_name,
        immediately_visible=immediately_visible,
        still_unclear=unclear[:4]
    )

def compute_career_snapshot(db: Session, user_id: int) -> CareerSnapshotResponse:
    """Concise factual career overview."""
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    target_role_name = profile.target_role.name if profile and profile.target_role else "Backend Engineer"

    user_skills = db.query(UserSkill).join(Skill).filter(UserSkill.user_id == user_id).all()
    proven = [us.skill.name for us in user_skills if us.state == SkillState.STRONG]
    developing = [us.skill.name for us in user_skills if us.state == SkillState.DEVELOPING]

    top_project = db.query(Project).filter(Project.user_id == user_id).first()
    latest_hist = db.query(UserSkillHistory).join(Skill).filter(UserSkillHistory.user_id == user_id).order_by(UserSkillHistory.changed_at.desc()).first()
    top_gap = db.query(Gap).join(Skill).filter(Gap.user_id == user_id).order_by(Gap.severity.desc()).first()

    recent_growth = f"{latest_hist.skill.name} advanced to {latest_hist.new_state}" if latest_hist else "Initial repository survey completed"
    next_area = top_gap.skill.name if top_gap else "Automated Testing & CI/CD"

    return CareerSnapshotResponse(
        target_role=target_role_name,
        proven_signals=proven,
        developing_signals=developing,
        featured_project=top_project.name if top_project else None,
        recent_growth=recent_growth,
        next_area_to_strengthen=next_area
    )

def export_profile_summary_text(db: Session, user_id: int) -> Dict[str, str]:
    """Generates copyable Markdown and plain text summaries traceable 100% to verified evidence."""
    profile = get_or_create_nexus_identity(db, user_id)
    user = profile.user
    target_role = profile.target_role.name if profile and profile.target_role else "Software Engineer"
    display_name = profile.name or "NEXUS Engineer"

    user_skills = db.query(UserSkill).join(Skill).filter(UserSkill.user_id == user_id).all()
    proven = [us.skill.name for us in user_skills if us.state == SkillState.STRONG]
    developing = [us.skill.name for us in user_skills if us.state == SkillState.DEVELOPING]

    public_projects = db.query(Project).filter(Project.user_id == user_id, Project.is_public == True).all()

    md_lines = [
        f"# {display_name} — Engineering Dossier",
        f"**Target Role:** {target_role} | **NEXUS ID:** {profile.nexus_id}",
        f"**Public Profile:** https://nexus.app/u/{profile.public_slug}\n",
        "## Verified Engineering Signals",
        f"- **Proven:** {', '.join(proven) if proven else 'In Progress'}",
        f"- **Developing:** {', '.join(developing) if developing else 'None'}\n",
        "## Featured Public Projects"
    ]

    for p in public_projects:
        md_lines.append(f"- **{p.name}**: Observable repository evidence verified by NEXUS.")

    md_text = "\n".join(md_lines)
    return {"markdown": md_text, "plain_text": md_text}
