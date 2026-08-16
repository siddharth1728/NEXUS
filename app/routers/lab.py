from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.lab import (
    ConceptSummarySchema, ConceptDetailSchema, LabDiscoveryFeedResponse
)
from app.services import lab_service

router = APIRouter(prefix="/lab", tags=["Engineering Lab"])

@router.get("/discovery", response_model=LabDiscoveryFeedResponse)
def get_todays_discovery(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return lab_service.get_lab_discovery_feed(current_user.id, db)

@router.get("/concepts", response_model=List[ConceptSummarySchema])
def get_concepts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return lab_service.get_all_concepts(current_user.id, db)

@router.get("/concepts/{concept_key}", response_model=ConceptDetailSchema)
def get_concept_detail(
    concept_key: str,
    project_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services import telemetry_service
    telemetry_service.record_event(
        db, "LAB_ACTIVITY_COMPLETED", user_id=current_user.id, 
        context={"concept_key": concept_key, "project_id": project_id}
    )
    return lab_service.get_concept_detail(concept_key, current_user.id, db, project_id=project_id)
