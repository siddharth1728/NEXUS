from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.ecosystem import (
    MentorInviteRequest, MentorInviteResponse, MentorAcceptRequest,
    MentorNoteCreateRequest, MentorNoteResponse, MentoredStudentSummary, MentoredStudentDossier,
    ReviewLinkCreateRequest, ReviewLinkResponse, ReviewProjectViewResponse,
    CohortCreateRequest, CohortJoinRequest, CohortSummary, EducatorObservatoryResponse,
    TeamCreateRequest, TeamJoinRequest, TeamShareProjectRequest, TeamCollaborationResponse,
    SharingCenterOverviewResponse
)
from app.services.ecosystem_service import (
    get_student_sharing_center,
    create_mentor_invitation, accept_mentor_invitation, revoke_mentor_relationship,
    list_mentored_students, get_mentored_student_dossier, add_mentor_note,
    create_project_review_link, get_project_review_by_token, revoke_review_link,
    create_cohort, list_educator_cohorts, join_cohort_as_student, get_cohort_observatory_analytics,
    create_team, join_team, share_project_to_team, get_team_collaboration_view,
    get_audience_preview, remove_team_member
)
from app.services import telemetry_service

router = APIRouter(prefix="/api/ecosystem", tags=["NEXUS Ecosystem"])

# ── Sharing Control Center ─────────────────────────────────

@router.get("/sharing", response_model=SharingCenterOverviewResponse)
def get_sharing_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns full sharing permissions ledger, active connections, and audit history."""
    return get_student_sharing_center(db, current_user.id)

# ── Mentor Endpoints ───────────────────────────────────────

@router.post("/mentor/invite", response_model=MentorInviteResponse, status_code=status.HTTP_201_CREATED)
def invite_mentor(
    payload: MentorInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a secure, single-use mentor invitation token with explicit permission scopes."""
    result = create_mentor_invitation(
        db, current_user.id, payload.mentor_email, payload.permissions, payload.expires_in_days
    )
    telemetry_service.record_event(db, "MENTOR_INVITED", user_id=current_user.id)
    return result

@router.post("/mentor/accept")
def accept_mentor(
    payload: MentorAcceptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accepts a mentor invitation and establishes a verified relationship."""
    rel = accept_mentor_invitation(db, current_user.id, payload.invite_token)
    telemetry_service.record_event(db, "MENTOR_ACCEPTED", user_id=current_user.id)
    return {"message": "Mentor invitation accepted", "relationship_id": rel.id}

@router.post("/mentor/revoke/{relationship_id}")
def revoke_mentor(
    relationship_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Instantly revokes mentor access."""
    revoke_mentor_relationship(db, current_user.id, relationship_id)
    return {"message": "Mentor access revoked immediately"}

@router.get("/mentor/students", response_model=List[MentoredStudentSummary])
def get_my_mentored_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all students actively mentored by the current user."""
    return list_mentored_students(db, current_user.id)

@router.get("/mentor/students/{student_id}", response_model=MentoredStudentDossier)
def get_student_dossier_for_mentor(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns student's evidence-backed dossier filtered strictly by granted permissions."""
    return get_mentored_student_dossier(db, current_user.id, student_id)

@router.post("/mentor/students/{student_id}/notes", response_model=MentorNoteResponse, status_code=status.HTTP_201_CREATED)
def create_mentor_note(
    student_id: int,
    payload: MentorNoteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Adds a private mentor guidance note."""
    return add_mentor_note(
        db, current_user.id, student_id, payload.note_text, payload.recommended_quest_id, payload.recommended_concept_key
    )

# ── Review Links Endpoints ─────────────────────────────────

@router.post("/review-links", response_model=ReviewLinkResponse, status_code=status.HTTP_201_CREATED)
def create_review_link(
    payload: ReviewLinkCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates a temporary, read-only project review link."""
    result = create_project_review_link(
        db, current_user.id, payload.project_id, payload.label, payload.expires_in_days
    )
    telemetry_service.record_event(db, "REVIEW_LINK_CREATED", user_id=current_user.id)
    return result

@router.get("/review/{token}", response_model=ReviewProjectViewResponse)
def get_project_review(
    token: str,
    db: Session = Depends(get_db)
):
    """Public read-only project review view using secure token."""
    return get_project_review_by_token(db, token)

@router.post("/review-links/revoke/{link_id}")
def revoke_review(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revokes a review link immediately."""
    revoke_review_link(db, current_user.id, link_id)
    return {"message": "Review link revoked"}

# ── Educator Observatory Endpoints ─────────────────────────

@router.post("/educator/cohorts", response_model=CohortSummary, status_code=status.HTTP_201_CREATED)
def create_new_cohort(
    payload: CohortCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new student cohort for an instructor."""
    return create_cohort(db, current_user.id, payload.name, payload.course_code)

@router.get("/educator/cohorts", response_model=List[CohortSummary])
def get_educator_cohorts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lists all cohorts managed by the instructor."""
    return list_educator_cohorts(db, current_user.id)

@router.post("/educator/cohorts/join")
def join_cohort(
    payload: CohortJoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Student joins a cohort using instructor's code."""
    join_cohort_as_student(db, current_user.id, payload.invite_code)
    return {"message": "Successfully joined cohort"}

@router.get("/educator/cohorts/{cohort_id}/analytics", response_model=EducatorObservatoryResponse)
def get_cohort_analytics(
    cohort_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns aggregated, privacy-preserving cohort observatory analytics."""
    return get_cohort_observatory_analytics(db, current_user.id, cohort_id)

# ── Team Collaboration Endpoints ───────────────────────────

@router.post("/teams", response_model=TeamCollaborationResponse, status_code=status.HTTP_201_CREATED)
def create_new_team(
    payload: TeamCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new collaboration team."""
    return create_team(db, current_user.id, payload.name, payload.description)

@router.post("/teams/join")
def join_team_endpoint(
    payload: TeamJoinRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Joins a team using an invite code."""
    join_team(db, current_user.id, payload.invite_code)
    return {"message": "Joined team successfully"}

@router.post("/teams/{team_id}/share-project")
def share_project_with_team(
    team_id: int,
    payload: TeamShareProjectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Shares a project repository with a team."""
    share_project_to_team(db, current_user.id, team_id, payload.project_id)
    return {"message": "Project shared with team"}

@router.get("/teams/{team_id}/collaboration", response_model=TeamCollaborationResponse)
def get_team_collaboration(
    team_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns collaboration signals for shared team projects."""
    return get_team_collaboration_view(db, current_user.id, team_id)

@router.get("/sharing/preview/{target_type}")
def get_sharing_audience_preview(
    target_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns a faithful simulated payload of what a target audience can observe."""
    return get_audience_preview(db, current_user.id, target_type)

@router.post("/teams/{team_id}/remove-member/{target_user_id}")
def remove_member_from_team(
    team_id: int,
    target_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Removes a member from a team."""
    remove_team_member(db, current_user.id, team_id, target_user_id)
    return {"message": "Member removed from team"}
