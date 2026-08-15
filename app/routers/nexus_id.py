from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.nexus_id import (
    PublicProfileResponse, PublicAtlasResponse,
    NexusIdSettingsResponse, NexusIdSettingsUpdate,
    ClaimCreateRequest, ClaimListResponse,
    PortfolioSelectorResponse, RecruiterViewResponse, CareerSnapshotResponse
)
from app.services.nexus_id_service import (
    get_public_profile_by_slug, get_public_atlas_by_slug,
    get_nexus_id_settings, update_nexus_id_settings,
    evaluate_user_claims, add_user_claim, delete_user_claim,
    compute_portfolio_selector, compute_recruiter_preview,
    compute_career_snapshot, export_profile_summary_text
)

router = APIRouter(tags=["NEXUS ID & Career Layer"])

# --- Public Endpoints (No Auth Required) ---

@router.get("/api/public-profiles/{slug}", response_model=PublicProfileResponse)
def get_public_profile(slug: str, db: Session = Depends(get_db)):
    """Returns the sanitized, evidence-backed public engineering passport for a given slug."""
    return get_public_profile_by_slug(db, slug)

@router.get("/api/public-profiles/{slug}/atlas", response_model=PublicAtlasResponse)
def get_public_atlas(slug: str, db: Session = Depends(get_db)):
    """Returns the public-safe projection of the Engineering Atlas for a given slug."""
    return get_public_atlas_by_slug(db, slug)

# --- Authenticated Owner Endpoints ---

@router.get("/api/profile/nexus-id", response_model=NexusIdSettingsResponse)
def get_owner_nexus_id_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns the authenticated owner's NEXUS ID settings and health checklist."""
    return get_nexus_id_settings(db, current_user.id)

@router.put("/api/profile/nexus-id", response_model=NexusIdSettingsResponse)
def update_owner_nexus_id_settings(
    payload: NexusIdSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates owner visibility, custom slug, bio, and featured projects with strict ownership validation."""
    return update_nexus_id_settings(db, current_user.id, payload)

# --- Career Layer: Claims vs Proof ---

@router.get("/api/career/claims", response_model=ClaimListResponse)
def get_career_claims(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Evaluates the student's self-declared claims against deterministic skill states and evidence."""
    return evaluate_user_claims(db, current_user.id)

@router.post("/api/career/claims", status_code=status.HTTP_201_CREATED)
def create_career_claim(
    payload: ClaimCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Adds a new claim to the student's Claim vs Proof workbench."""
    claim = add_user_claim(db, current_user.id, payload.claim_text, payload.category)
    return {"message": "Claim registered for verification", "id": claim.id, "claim_text": claim.claim_text}

@router.delete("/api/career/claims/{claim_id}")
def remove_career_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes a claim from the student's workbench."""
    delete_user_claim(db, current_user.id, claim_id)
    return {"message": "Claim removed"}

# --- Career Layer: Portfolio Selector & Recruiter View ---

@router.get("/api/career/portfolio-selector", response_model=PortfolioSelectorResponse)
def get_portfolio_selector(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deterministically identifies the best project for the student's target role."""
    return compute_portfolio_selector(db, current_user.id)

@router.get("/api/career/recruiter-view", response_model=RecruiterViewResponse)
def get_recruiter_view(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clarity preview of what is immediately visible on the passport vs what is still unclear."""
    return compute_recruiter_preview(db, current_user.id)

@router.get("/api/career/snapshot", response_model=CareerSnapshotResponse)
def get_career_snapshot(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Concise factual career summary."""
    return compute_career_snapshot(db, current_user.id)

@router.get("/api/career/export")
def export_dossier(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exports structured, evidence-traceable dossier summaries in Markdown and plain-text."""
    return export_profile_summary_text(db, current_user.id)
