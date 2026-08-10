from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.profile import StudentProfile
from app.schemas.profile import ProfileUpdate
from app.models.user import User

def get_profile(db: Session, user_id: int) -> StudentProfile:
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == user_id).first()
    # Create empty profile if none exists
    if not profile:
        profile = StudentProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

def update_profile(db: Session, user_id: int, profile_data: ProfileUpdate) -> StudentProfile:
    profile = get_profile(db, user_id)
    
    if profile_data.target_role_id is not None:
        profile.target_role_id = profile_data.target_role_id
    if profile_data.github_username is not None:
        profile.github_username = profile_data.github_username
        
    db.commit()
    db.refresh(profile)
    return profile
