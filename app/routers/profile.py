from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.schemas.profile import ProfileResponse, ProfileUpdate, SettingsUpdate
from app.services import profile_service
from app.dependencies.auth import get_current_user
from app.core.csrf import verify_csrf_token
from app.models.user import User

router = APIRouter()

@router.get("", response_model=ProfileResponse)
def get_my_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = profile_service.get_profile(db, current_user.id)
    return profile_service.profile_to_response(profile, current_user)

@router.put("", response_model=ProfileResponse, dependencies=[Depends(verify_csrf_token)])
def update_my_profile(profile_data: ProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = profile_service.update_profile(db, current_user.id, profile_data)
    return profile_service.profile_to_response(profile, current_user)

@router.put("/settings", response_model=ProfileResponse, dependencies=[Depends(verify_csrf_token)])
def update_my_settings(settings_data: SettingsUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = profile_service.update_settings(db, current_user.id, settings_data)
    return profile_service.profile_to_response(profile, current_user)

@router.get("/export")
def export_my_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = profile_service.get_profile(db, current_user.id)
    # Simple export format for now
    data = {
        "user": {
            "email": current_user.email,
        },
        "profile": {
            "github_username": profile.github_username,
            "target_role": profile.target_role.name if profile.target_role else None,
            "preferences": {
                "notify_weekly_report": profile.notify_weekly_report,
                "notify_gap_alerts": profile.notify_gap_alerts,
                "public_profile": profile.public_profile,
                "show_raw_github_stats": profile.show_raw_github_stats
            }
        },
        "skills": [], # We can expand this later to pull actual skills
        "evidence": [] 
    }
    return data

@router.delete("/account", dependencies=[Depends(verify_csrf_token)])
def delete_my_account(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db.delete(current_user)
    db.commit()
    return {"status": "success", "message": "Account deleted"}
