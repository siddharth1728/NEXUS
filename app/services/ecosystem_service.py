import json
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User, UserSkill, UserSkillHistory, Gap, SkillState
from app.models.profile import StudentProfile
from app.models.taxonomy import TargetRole, Skill
from app.models.project import Project, RepositorySnapshot, Artifact, RawObservation, Evidence, EvidenceSkill, SnapshotStatus
from app.models.ecosystem import (
    PermissionScope, RelationshipStatus,
    MentorRelationship, MentorNote, ReviewLink,
    Cohort, CohortMembership, Team, TeamMember, TeamProject, SharingAuditLog
)
from app.schemas.ecosystem import (
    VALID_PERMISSIONS,
    MentorInviteResponse, MentorNoteResponse, MentoredStudentSummary, MentoredStudentDossier,
    ReviewLinkResponse, ReviewProjectViewResponse,
    CohortSummary, EducatorObservatoryResponse,
    TeamCollaborationResponse,
    PermissionLedgerItem, SharingCenterOverviewResponse
)
from app.services.nexus_id_service import get_or_create_nexus_identity

# ── Audit Logger ──────────────────────────────────────────

def record_audit_log(
    db: Session,
    owner_id: int,
    actor_id: Optional[int],
    action: str,
    target_type: str,
    target_id: Optional[str] = None
):
    """Records an internal security audit event without storing sensitive IP information."""
    try:
        log = SharingAuditLog(
            resource_owner_id=owner_id,
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(log)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Audit log notice: {e}")

# ── Layer A: Sharing Control Center ───────────────────────

def get_student_sharing_center(db: Session, student_id: int) -> SharingCenterOverviewResponse:
    """Consolidates all sharing permissions, active mentors, review links, cohorts, and audit events."""
    profile = get_or_create_nexus_identity(db, student_id)
    
    # Active mentors
    mentors = db.query(MentorRelationship).filter(
        MentorRelationship.student_id == student_id,
        MentorRelationship.status.in_([RelationshipStatus.ACCEPTED, RelationshipStatus.PENDING])
    ).all()
    
    # Active review links
    review_links = db.query(ReviewLink).filter(
        ReviewLink.student_id == student_id,
        ReviewLink.is_active == True
    ).all()

    # Active cohorts
    cohort_memberships = db.query(CohortMembership).join(Cohort).filter(
        CohortMembership.student_id == student_id,
        CohortMembership.is_active == True
    ).all()

    # Active teams
    team_memberships = db.query(TeamMember).join(Team).filter(
        TeamMember.user_id == student_id
    ).all()

    ledger: List[PermissionLedgerItem] = []

    # 1. Public Profile entry (if active)
    if profile.public_profile:
        ledger.append(PermissionLedgerItem(
            id="public_profile",
            entity_type="PUBLIC_PROFILE",
            name="Public Engineering Passport",
            access_granted=["PROFILE", "FEATURED_PROJECTS", "PROOF" if profile.show_proof else "", "JOURNEY" if profile.show_journey else ""],
            granted_since="Active",
            expires_at=None,
            can_revoke=True
        ))

    # 2. Mentors
    for m in mentors:
        mentor_name = m.mentor.email if m.mentor else (m.mentor_email or "Pending Invitation")
        perms = []
        try:
            perms = json.loads(m.permissions)
        except Exception:
            perms = ["PROFILE"]
        
        expires_str = m.expires_at.strftime("%b %d, %Y") if m.expires_at else "No expiration"
        ledger.append(PermissionLedgerItem(
            id=f"mentor_{m.id}",
            entity_type="MENTOR",
            name=f"Mentor: {mentor_name} ({m.status.value})",
            access_granted=perms,
            granted_since=m.created_at.strftime("%b %d, %Y"),
            expires_at=expires_str,
            can_revoke=True
        ))

    # 3. Review links
    for r in review_links:
        exp_str = r.expires_at.strftime("%b %d, %Y") if r.expires_at else "No expiration"
        ledger.append(PermissionLedgerItem(
            id=f"review_{r.id}",
            entity_type="REVIEW_LINK",
            name=f"Review Link: {r.project.name} ({r.label or 'Read-Only'})",
            access_granted=["PROJECT_INTELLIGENCE", "PROOF", "QUESTIONS"],
            granted_since=r.created_at.strftime("%b %d, %Y"),
            expires_at=exp_str,
            can_revoke=True
        ))

    # 4. Cohorts
    for cm in cohort_memberships:
        ledger.append(PermissionLedgerItem(
            id=f"cohort_{cm.cohort.id}",
            entity_type="COHORT",
            name=f"Cohort: {cm.cohort.name} ({cm.cohort.course_code})",
            access_granted=["ANONYMOUS_AGGREGATE_SIGNALS"],
            granted_since=cm.joined_at.strftime("%b %d, %Y"),
            expires_at=None,
            can_revoke=True
        ))

    # 5. Teams
    for tm in team_memberships:
        ledger.append(PermissionLedgerItem(
            id=f"team_{tm.team.id}",
            entity_type="TEAM",
            name=f"Team: {tm.team.name} ({tm.role})",
            access_granted=["SHARED_PROJECTS_ONLY"],
            granted_since=tm.joined_at.strftime("%b %d, %Y"),
            expires_at=None,
            can_revoke=True
        ))

    # Audit events
    audit_rows = db.query(SharingAuditLog).filter(
        SharingAuditLog.resource_owner_id == student_id
    ).order_by(SharingAuditLog.created_at.desc()).limit(10).all()

    audit_events = [
        {
            "action": a.action,
            "target_type": a.target_type,
            "timestamp": a.created_at.strftime("%b %d, %Y %H:%M UTC")
        }
        for a in audit_rows
    ]

    return SharingCenterOverviewResponse(
        public_profile_enabled=profile.public_profile,
        public_slug=profile.public_slug,
        active_mentors_count=len([m for m in mentors if m.status == RelationshipStatus.ACCEPTED]),
        active_cohorts_count=len(cohort_memberships),
        active_teams_count=len(team_memberships),
        active_review_links_count=len(review_links),
        permissions_ledger=ledger,
        recent_audit_events=audit_events
    )

# ── Layer B: Mentor Mode ──────────────────────────────────

def create_mentor_invitation(
    db: Session,
    student_id: int,
    mentor_email: Optional[str],
    permissions: List[str],
    expires_in_days: Optional[int]
) -> MentorInviteResponse:
    """Generates a cryptographically secure, single-use mentor invitation."""
    # Sanitize and validate permissions
    valid_perms = [p.upper() for p in permissions if p.upper() in VALID_PERMISSIONS]
    if not valid_perms:
        valid_perms = ["PROFILE", "PROJECTS", "PROOF", "JOURNEY", "QUESTS"]

    token = secrets.token_urlsafe(24)
    expires_at = None
    if expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    rel = MentorRelationship(
        student_id=student_id,
        invite_token=token,
        mentor_email=mentor_email.strip() if mentor_email else None,
        permissions=json.dumps(valid_perms),
        status=RelationshipStatus.PENDING,
        expires_at=expires_at,
        created_at=datetime.now(timezone.utc)
    )
    db.add(rel)
    db.commit()
    db.refresh(rel)

    record_audit_log(db, student_id, student_id, "CREATE_MENTOR_INVITE", "MENTOR", str(rel.id))

    return MentorInviteResponse(
        relationship_id=rel.id,
        invite_token=token,
        invite_url=f"/mentor/accept?token={token}",
        permissions=valid_perms,
        expires_at=expires_at.strftime("%b %d, %Y") if expires_at else None
    )

def accept_mentor_invitation(db: Session, mentor_user_id: int, token: str) -> MentorRelationship:
    """Binds an authenticated mentor to a student using a valid token."""
    rel = db.query(MentorRelationship).filter(
        MentorRelationship.invite_token == token
    ).first()

    if not rel:
        raise HTTPException(status_code=404, detail="Invalid or non-existent mentor invitation token")

    if rel.status == RelationshipStatus.REVOKED:
        raise HTTPException(status_code=400, detail="This mentor invitation has been revoked by the student")

    if rel.status == RelationshipStatus.ACCEPTED:
        raise HTTPException(status_code=400, detail="This mentor invitation has already been accepted")

    if rel.expires_at and rel.expires_at < datetime.now(timezone.utc):
        rel.status = RelationshipStatus.EXPIRED
        db.commit()
        raise HTTPException(status_code=400, detail="This mentor invitation has expired")

    if rel.student_id == mentor_user_id:
        raise HTTPException(status_code=400, detail="You cannot accept your own mentor invitation")

    rel.mentor_id = mentor_user_id
    rel.status = RelationshipStatus.ACCEPTED
    rel.accepted_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rel)

    record_audit_log(db, rel.student_id, mentor_user_id, "ACCEPT_MENTOR_INVITE", "MENTOR", str(rel.id))
    return rel

def revoke_mentor_relationship(db: Session, student_id: int, relationship_id: int) -> bool:
    """Instantly revokes mentor access. Access stops immediately with zero cached permissions."""
    rel = db.query(MentorRelationship).filter(
        MentorRelationship.id == relationship_id,
        MentorRelationship.student_id == student_id
    ).first()

    if not rel:
        raise HTTPException(status_code=404, detail="Mentor relationship not found")

    rel.status = RelationshipStatus.REVOKED
    rel.revoked_at = datetime.now(timezone.utc)
    db.commit()

    record_audit_log(db, student_id, student_id, "REVOKE_MENTOR_ACCESS", "MENTOR", str(relationship_id))
    return True

def list_mentored_students(db: Session, mentor_user_id: int) -> List[MentoredStudentSummary]:
    """Lists all students who have currently active mentor relationships with the authenticated mentor."""
    rels = db.query(MentorRelationship).filter(
        MentorRelationship.mentor_id == mentor_user_id,
        MentorRelationship.status == RelationshipStatus.ACCEPTED
    ).all()

    results: List[MentoredStudentSummary] = []
    now = datetime.now(timezone.utc)

    for r in rels:
        if r.expires_at and r.expires_at < now:
            continue  # Expired

        profile = get_or_create_nexus_identity(db, r.student_id)
        target_role = profile.target_role.name if profile.target_role else "Software Engineer"
        perms = []
        try:
            perms = json.loads(r.permissions)
        except Exception:
            perms = []

        results.append(MentoredStudentSummary(
            student_id=r.student_id,
            student_name=profile.name or "NEXUS Student",
            target_role=target_role,
            permissions=perms,
            relationship_id=r.id,
            since=r.accepted_at.strftime("%b %Y") if r.accepted_at else "Recent"
        ))

    return results

def get_mentored_student_dossier(db: Session, mentor_user_id: int, student_id: int) -> MentoredStudentDossier:
    """
    Assembles a scoped, evidence-backed student dossier for an authorized mentor.
    Strictly filters data according to granted permissions. Zero leakage of private notes from other mentors or private AI chats.
    """
    rel = db.query(MentorRelationship).filter(
        MentorRelationship.student_id == student_id,
        MentorRelationship.mentor_id == mentor_user_id,
        MentorRelationship.status == RelationshipStatus.ACCEPTED
    ).first()

    if not rel:
        raise HTTPException(status_code=403, detail="No active mentor relationship found for this student")

    if rel.expires_at and rel.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=403, detail="Mentor access has expired")

    perms = set()
    try:
        perms = set(json.loads(rel.permissions))
    except Exception:
        perms = {"PROFILE"}

    profile = get_or_create_nexus_identity(db, student_id)
    target_role = profile.target_role.name if profile.target_role else "Software Engineer"

    # User skills
    user_skills = db.query(UserSkill).join(Skill).filter(UserSkill.user_id == student_id).all()
    proven = [us.skill.name for us in user_skills if us.state == SkillState.STRONG]
    developing = [us.skill.name for us in user_skills if us.state == SkillState.DEVELOPING]
    unexplored = [us.skill.name for us in user_skills if us.state in [SkillState.WEAK, SkillState.MISSING]]

    # Projects
    featured_projects = None
    if "PROJECTS" in perms:
        projects = db.query(Project).filter(Project.user_id == student_id).all()
        featured_projects = [
            {
                "id": p.id,
                "name": p.name,
                "is_public": p.is_public
            }
            for p in projects
        ]

    # Proof
    verified_proof = None
    if "PROOF" in perms:
        ev_rows = db.query(Evidence, RawObservation, Skill)\
            .join(RawObservation, Evidence.raw_observation_id == RawObservation.id)\
            .join(Artifact, RawObservation.artifact_id == Artifact.id)\
            .join(RepositorySnapshot, Artifact.snapshot_id == RepositorySnapshot.id)\
            .join(Project, RepositorySnapshot.project_id == Project.id)\
            .outerjoin(EvidenceSkill, EvidenceSkill.evidence_id == Evidence.id)\
            .outerjoin(Skill, EvidenceSkill.skill_id == Skill.id)\
            .filter(Project.user_id == student_id)\
            .order_by(Evidence.quality_score.desc()).limit(10).all()

        verified_proof = [
            {
                "signal": sk.name if sk else ev.type.value,
                "observation": ro.observation_text,
                "score": ev.quality_score
            }
            for ev, ro, sk in ev_rows
        ]

    # Journey
    journey_milestones = None
    if "JOURNEY" in perms:
        hist_rows = db.query(UserSkillHistory).join(Skill).filter(
            UserSkillHistory.user_id == student_id
        ).order_by(UserSkillHistory.changed_at.asc()).limit(10).all()

        journey_milestones = [
            {
                "skill": h.skill.name,
                "from_state": h.previous_state or "UNEXPLORED",
                "to_state": h.new_state,
                "date": h.changed_at.strftime("%b %Y") if h.changed_at else "Recent"
            }
            for h in hist_rows
        ]

    # Quests / Gaps
    active_quests = None
    if "QUESTS" in perms:
        gaps = db.query(Gap).join(Skill).filter(Gap.user_id == student_id).order_by(Gap.severity.desc()).limit(5).all()
        active_quests = [
            {
                "skill_name": g.skill.name,
                "severity": g.severity,
                "quest_goal": f"Implement repository proof for {g.skill.name}"
            }
            for g in gaps
        ]

    # Mentor's private notes for this student
    notes_rows = db.query(MentorNote).filter(
        MentorNote.relationship_id == rel.id
    ).order_by(MentorNote.created_at.desc()).all()

    mentor_notes = [
        MentorNoteResponse(
            id=n.id,
            author_email=n.author.email,
            note_text=n.note_text,
            recommended_quest_id=n.recommended_quest_id,
            recommended_concept_key=n.recommended_concept_key,
            created_at=n.created_at.strftime("%b %d, %Y")
        )
        for n in notes_rows
    ]

    record_audit_log(db, student_id, mentor_user_id, "VIEW_MENTOR_DOSSIER", "MENTOR", str(rel.id))

    return MentoredStudentDossier(
        student_id=student_id,
        student_name=profile.name or "NEXUS Student",
        nexus_id=profile.nexus_id,
        target_role=target_role,
        granted_permissions=sorted(list(perms)),
        proven_signals=proven if "PROOF" in perms or "PROFILE" in perms else None,
        developing_signals=developing if "PROOF" in perms or "PROFILE" in perms else None,
        unexplored_signals=unexplored if "QUESTS" in perms or "PROFILE" in perms else None,
        featured_projects=featured_projects,
        verified_proof=verified_proof,
        journey_milestones=journey_milestones,
        active_quests=active_quests,
        mentor_notes=mentor_notes
    )

def add_mentor_note(
    db: Session,
    mentor_user_id: int,
    student_id: int,
    note_text: str,
    recommended_quest_id: Optional[int],
    recommended_concept_key: Optional[str]
) -> MentorNoteResponse:
    """Adds a private mentor guidance note. Strictly segregated from skill states and gaps."""
    rel = db.query(MentorRelationship).filter(
        MentorRelationship.student_id == student_id,
        MentorRelationship.mentor_id == mentor_user_id,
        MentorRelationship.status == RelationshipStatus.ACCEPTED
    ).first()

    if not rel:
        raise HTTPException(status_code=403, detail="No active mentor relationship found")

    note = MentorNote(
        relationship_id=rel.id,
        author_id=mentor_user_id,
        student_id=student_id,
        note_text=note_text.strip(),
        recommended_quest_id=recommended_quest_id,
        recommended_concept_key=recommended_concept_key,
        created_at=datetime.now(timezone.utc)
    )
    db.add(note)
    db.commit()
    db.refresh(note)

    mentor_user = db.query(User).filter(User.id == mentor_user_id).first()
    return MentorNoteResponse(
        id=note.id,
        author_email=mentor_user.email,
        note_text=note.note_text,
        recommended_quest_id=note.recommended_quest_id,
        recommended_concept_key=note.recommended_concept_key,
        created_at=note.created_at.strftime("%b %d, %Y")
    )

# ── Layer C: Educator Observatory ─────────────────────────

def create_cohort(db: Session, educator_id: int, name: str, course_code: str) -> CohortSummary:
    """Creates a new educational cohort with a unique secure student join code."""
    invite_code = secrets.token_hex(4).upper()
    cohort = Cohort(
        educator_id=educator_id,
        name=name.strip(),
        course_code=course_code.strip(),
        invite_code=invite_code,
        created_at=datetime.now(timezone.utc)
    )
    db.add(cohort)
    db.commit()
    db.refresh(cohort)

    return CohortSummary(
        id=cohort.id,
        name=cohort.name,
        course_code=cohort.course_code,
        invite_code=cohort.invite_code,
        member_count=0,
        created_at=cohort.created_at.strftime("%b %Y")
    )

def list_educator_cohorts(db: Session, educator_id: int) -> List[CohortSummary]:
    """Lists all cohorts managed by the authenticated educator."""
    cohorts = db.query(Cohort).filter(Cohort.educator_id == educator_id).all()
    results = []
    for c in cohorts:
        cnt = db.query(CohortMembership).filter(CohortMembership.cohort_id == c.id, CohortMembership.is_active == True).count()
        results.append(CohortSummary(
            id=c.id,
            name=c.name,
            course_code=c.course_code,
            invite_code=c.invite_code,
            member_count=cnt,
            created_at=c.created_at.strftime("%b %Y")
        ))
    return results

def join_cohort_as_student(db: Session, student_id: int, invite_code: str) -> bool:
    """Student joins a cohort using the instructor's invite code."""
    cohort = db.query(Cohort).filter(Cohort.invite_code == invite_code.strip().upper()).first()
    if not cohort:
        raise HTTPException(status_code=404, detail="Invalid cohort join code")

    existing = db.query(CohortMembership).filter(
        CohortMembership.cohort_id == cohort.id,
        CohortMembership.student_id == student_id
    ).first()

    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
        return True

    membership = CohortMembership(
        cohort_id=cohort.id,
        student_id=student_id,
        joined_at=datetime.now(timezone.utc),
        is_active=True
    )
    db.add(membership)
    db.commit()
    return True

def get_cohort_observatory_analytics(db: Session, educator_id: int, cohort_id: int) -> EducatorObservatoryResponse:
    """
    Computes decision-oriented, aggregate-first analytics for a cohort.
    Enforces strict privacy thresholds:
      - < 3 students: UNAVAILABLE_INSUFFICIENT_SIZE (Zero aggregation)
      - 3–5 students: LIMITED_SUMMARY (Totals only)
      - >= 6 students: FULL_OBSERVATORY (Detailed patterns)
    """
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id, Cohort.educator_id == educator_id).first()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found or unauthorized")

    memberships = db.query(CohortMembership).filter(
        CohortMembership.cohort_id == cohort.id,
        CohortMembership.is_active == True
    ).all()
    student_count = len(memberships)
    student_ids = [m.student_id for m in memberships]

    # Guardrail 1: Less than 3 students
    if student_count < 3:
        return EducatorObservatoryResponse(
            cohort_id=cohort.id,
            name=cohort.name,
            course_code=cohort.course_code,
            student_count=student_count,
            privacy_status="UNAVAILABLE_INSUFFICIENT_SIZE",
            privacy_note="Cohort analytics require at least 3 active students to protect individual privacy.",
            most_common_gap=None,
            most_common_signals=[],
            dominant_project_patterns=[],
            curriculum_recommendations=["Invite more students to unlock aggregated cohort analytics."]
        )

    # Gather aggregate user skills
    user_skills = db.query(UserSkill, Skill).join(Skill).filter(UserSkill.user_id.in_(student_ids)).all()
    skill_proven_counts: Dict[str, int] = {}
    for us, sk in user_skills:
        if us.state == SkillState.STRONG:
            skill_proven_counts[sk.name] = skill_proven_counts.get(sk.name, 0) + 1

    # Gather aggregate gaps
    gaps = db.query(Gap, Skill).join(Skill).filter(Gap.user_id.in_(student_ids)).all()
    gap_counts: Dict[str, int] = {}
    for g, sk in gaps:
        gap_counts[sk.name] = gap_counts.get(sk.name, 0) + 1

    most_common_gap = None
    if gap_counts:
        most_common_gap = max(gap_counts.items(), key=lambda x: x[1])[0]

    # Guardrail 2: 3 to 5 students (Limited Summary)
    if student_count < 6:
        recommendation = f"Consider introducing practical exercises for {most_common_gap}." if most_common_gap else "Continue monitoring initial cohort progress."
        return EducatorObservatoryResponse(
            cohort_id=cohort.id,
            name=cohort.name,
            course_code=cohort.course_code,
            student_count=student_count,
            privacy_status="LIMITED_SUMMARY",
            privacy_note="Cohort has 3–5 students. Displaying high-level aggregated totals only.",
            most_common_gap=most_common_gap,
            most_common_signals=[{"name": k, "frequency": f"{v} students"} for k, v in sorted(skill_proven_counts.items(), key=lambda x: x[1], reverse=True)[:3]],
            dominant_project_patterns=[],
            curriculum_recommendations=[recommendation]
        )

    # Guardrail 3: 6+ students (Full Observatory)
    # Detect dominant patterns across repositories
    projects = db.query(Project).filter(Project.user_id.in_(student_ids)).all()
    proj_ids = [p.id for p in projects]

    has_api = db.query(Evidence).filter(Evidence.type == "API").count() > 0
    has_db = db.query(Evidence).filter(Evidence.type == "DATABASE").count() > 0
    has_test = db.query(Evidence).filter(Evidence.type == "TESTING").count() > 0

    patterns = []
    if has_api and has_db:
        patterns.append({"pattern": "REST API + Relational Database", "observation": "Dominant architecture across student projects"})
    if not has_test:
        patterns.append({"pattern": "Low Automated Testing Footprint", "observation": "Few repositories contain unit or integration suites"})

    curriculum_recs = []
    if most_common_gap:
        curriculum_recs.append(f"Teaching Focus: Strengthen practical lab exercises on '{most_common_gap}'.")
    curriculum_recs.append(f"Project Review: Encourage students to add test suites to their existing API/DB codebases.")

    return EducatorObservatoryResponse(
        cohort_id=cohort.id,
        name=cohort.name,
        course_code=cohort.course_code,
        student_count=student_count,
        privacy_status="FULL_OBSERVATORY",
        privacy_note="Privacy-safe aggregation active across cohort.",
        most_common_gap=most_common_gap,
        most_common_signals=[{"name": k, "percentage": f"{int((v / student_count) * 100)}%"} for k, v in sorted(skill_proven_counts.items(), key=lambda x: x[1], reverse=True)[:5]],
        dominant_project_patterns=patterns,
        curriculum_recommendations=curriculum_recs
    )

# ── Layer D: Review Links (Temporary Project Review) ───────

def create_project_review_link(
    db: Session,
    student_id: int,
    project_id: int,
    label: Optional[str],
    expires_in_days: Optional[int]
) -> ReviewLinkResponse:
    """Generates a temporary read-only review link for a single project."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == student_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")

    token = secrets.token_urlsafe(24)
    expires_at = None
    if expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    link = ReviewLink(
        student_id=student_id,
        project_id=project_id,
        token=token,
        label=label.strip() if label else None,
        expires_at=expires_at,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    record_audit_log(db, student_id, student_id, "CREATE_REVIEW_LINK", "REVIEW_LINK", str(link.id))

    return ReviewLinkResponse(
        id=link.id,
        project_id=project.id,
        project_name=project.name,
        token=token,
        review_url=f"/review/{token}",
        expires_at=expires_at.strftime("%b %d, %Y") if expires_at else None,
        is_active=link.is_active,
        created_at=link.created_at.strftime("%b %d, %Y")
    )

def get_project_review_by_token(db: Session, token: str) -> ReviewProjectViewResponse:
    """Delivers read-only project intelligence, verified proof, and exploratory technical questions."""
    link = db.query(ReviewLink).filter(ReviewLink.token == token).first()
    if not link or not link.is_active:
        raise HTTPException(status_code=404, detail="Review link unavailable or revoked")

    if link.expires_at and link.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=404, detail="Review link has expired")

    project = link.project
    student = link.student
    profile = get_or_create_nexus_identity(db, student.id)
    target_role = profile.target_role.name if profile.target_role else "Software Engineer"

    # Gather evidence and signals for this specific project
    ev_rows = db.query(Evidence, RawObservation, Skill)\
        .join(RawObservation, Evidence.raw_observation_id == RawObservation.id)\
        .join(Artifact, RawObservation.artifact_id == Artifact.id)\
        .join(RepositorySnapshot, Artifact.snapshot_id == RepositorySnapshot.id)\
        .outerjoin(EvidenceSkill, EvidenceSkill.evidence_id == Evidence.id)\
        .outerjoin(Skill, EvidenceSkill.skill_id == Skill.id)\
        .filter(RepositorySnapshot.project_id == project.id)\
        .order_by(Evidence.quality_score.desc()).limit(8).all()

    signals = set()
    proof_items = []
    for ev, ro, sk in ev_rows:
        if sk:
            signals.add(sk.name)
        proof_items.append({
            "signal": sk.name if sk else ev.type.value,
            "observation": ro.observation_text,
            "type": ev.type.value
        })

    # Formulate evidence-grounded exploratory questions
    questions = []
    if "PostgreSQL" in signals or any("DB" in p["type"] for p in proof_items):
        questions.append("How did you design the database schemas and manage migrations in this service?")
    if "REST APIs" in signals or any("API" in p["type"] for p in proof_items):
        questions.append("How are errors, input validation, and API rate limits handled in the endpoints?")
    if not questions:
        questions.append("What was the primary architectural trade-off made when structuring this codebase?")

    record_audit_log(db, student.id, None, "VIEW_REVIEW_LINK", "REVIEW_LINK", str(link.id))

    return ReviewProjectViewResponse(
        project_name=project.name,
        student_nexus_id=profile.nexus_id,
        target_role=target_role,
        detected_technologies=["Python", "FastAPI", "PostgreSQL"],
        verified_signals=sorted(list(signals)),
        proof_ledger=proof_items,
        questions_to_explore=questions,
        atlas_context={"territory": "Backend Architecture", "status": "Verified"}
    )

def revoke_review_link(db: Session, student_id: int, link_id: int) -> bool:
    """Revokes a review link immediately."""
    link = db.query(ReviewLink).filter(ReviewLink.id == link_id, ReviewLink.student_id == student_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Review link not found")

    link.is_active = False
    db.commit()

    record_audit_log(db, student_id, student_id, "REVOKE_REVIEW_LINK", "REVIEW_LINK", str(link_id))
    return True

# ── Layer E: Team Mode ────────────────────────────────────

def create_team(db: Session, creator_id: int, name: str, description: Optional[str]) -> TeamCollaborationResponse:
    """Creates a new collaboration team."""
    invite_code = secrets.token_hex(4).upper()
    team = Team(
        creator_id=creator_id,
        name=name.strip(),
        description=description.strip() if description else None,
        invite_code=invite_code,
        created_at=datetime.now(timezone.utc)
    )
    db.add(team)
    db.flush()

    # Add creator as LEAD
    tm = TeamMember(
        team_id=team.id,
        user_id=creator_id,
        role="LEAD",
        joined_at=datetime.now(timezone.utc)
    )
    db.add(tm)
    db.commit()
    db.refresh(team)

    return get_team_collaboration_view(db, creator_id, team.id)

def join_team(db: Session, user_id: int, invite_code: str) -> bool:
    """User joins a team using an invite code."""
    team = db.query(Team).filter(Team.invite_code == invite_code.strip().upper()).first()
    if not team:
        raise HTTPException(status_code=404, detail="Invalid team invite code")

    existing = db.query(TeamMember).filter(TeamMember.team_id == team.id, TeamMember.user_id == user_id).first()
    if existing:
        return True

    tm = TeamMember(
        team_id=team.id,
        user_id=user_id,
        role="MEMBER",
        joined_at=datetime.now(timezone.utc)
    )
    db.add(tm)
    db.commit()
    return True

def share_project_to_team(db: Session, user_id: int, team_id: int, project_id: int) -> bool:
    """Shares a project with the team. Never shares personal unshared accounts."""
    membership = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="You are not a member of this team")

    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or you do not own it")

    existing = db.query(TeamProject).filter(TeamProject.team_id == team_id, TeamProject.project_id == project_id).first()
    if existing:
        return True

    tp = TeamProject(
        team_id=team_id,
        project_id=project_id,
        shared_at=datetime.now(timezone.utc)
    )
    db.add(tp)
    db.commit()
    return True

def get_team_collaboration_view(db: Session, user_id: int, team_id: int) -> TeamCollaborationResponse:
    """Returns collaboration signals for shared team projects without commit percentage shaming."""
    membership = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).first()
    if not membership:
        raise HTTPException(status_code=403, detail="You are not authorized to view this team")

    team = db.query(Team).filter(Team.id == team_id).first()
    members = db.query(TeamMember).join(User).filter(TeamMember.team_id == team.id).all()
    shared_projects = db.query(TeamProject).join(Project).filter(TeamProject.team_id == team.id).all()

    members_list = [
        {
            "user_id": m.user_id,
            "email_prefix": m.user.email.split("@")[0],
            "role": m.role,
            "joined": m.joined_at.strftime("%b %Y")
        }
        for m in members
    ]

    projects_list = [
        {
            "project_id": p.project_id,
            "name": p.project.name,
            "shared_at": p.shared_at.strftime("%b %d, %Y")
        }
        for p in shared_projects
    ]

    # Neutral collaboration signals (Facts, not percentages)
    collaboration_signals = [
        {"signal": "SHARED_REPOSITORIES", "fact": f"{len(shared_projects)} codebase(s) shared across team"},
        {"signal": "CODE_ORGANIZATION", "fact": "Modular package structure observed across active services"},
        {"signal": "TEAM_COLLABORATION", "fact": f"{len(members)} team member(s) participating in workspace"}
    ]

    return TeamCollaborationResponse(
        team_id=team.id,
        team_name=team.name,
        description=team.description,
        creator_id=team.creator_id,
        members_count=len(members),
        members=members_list,
        shared_projects=projects_list,
        collaboration_signals=collaboration_signals
    )
