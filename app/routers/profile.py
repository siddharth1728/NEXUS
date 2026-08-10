from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services import profile_service
from app.dependencies.auth import get_current_user
from app.core.csrf import verify_csrf_token

router = APIRouter()

@router.get("", response_model=ProfileResponse)
def get_my_profile(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Strictly scoped to the authenticated user's ID
    return profile_service.get_profile(db, current_user.id)

@router.put("", response_model=ProfileResponse, dependencies=[Depends(verify_csrf_token)])
def update_my_profile(profile_data: ProfileUpdate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Strictly scoped to the authenticated user's ID
    return profile_service.update_profile(db, current_user.id, profile_data)
