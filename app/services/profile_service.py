from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from app.models.profile import StudentProfile
from app.schemas.profile import ProfileUpdate, ProfileResponse
from app.models.user import User
from app.models.taxonomy import TargetRole

def get_profile(db: Session, user_id: int) -> StudentProfile:
    profile = (
        db.query(StudentProfile)
        .options(joinedload(StudentProfile.target_role))
        .filter(StudentProfile.user_id == user_id)
        .first()
    )
    # Create empty profile if none exists
    if not profile:
        profile = StudentProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile

def update_profile(db: Session, user_id: int, profile_data: ProfileUpdate) -> StudentProfile:
    profile = get_profile(db, user_id)

    if profile_data.target_role is not None:
        if profile_data.target_role.strip() == "":
            profile.target_role_id = None
        else:
            role = db.query(TargetRole).filter(TargetRole.name == profile_data.target_role.strip()).first()
            if not role:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown target role")
            profile.target_role_id = role.id

    if profile_data.target_role_id is not None:
        profile.target_role_id = profile_data.target_role_id
    if profile_data.github_username is not None:
        profile.github_username = profile_data.github_username
    if profile_data.name is not None:
        profile.name = profile_data.name

    db.commit()
    return get_profile(db, user_id)

from app.schemas.profile import ProfileUpdate, ProfileResponse, SettingsUpdate

def update_settings(db: Session, user_id: int, settings_data: SettingsUpdate) -> StudentProfile:
    profile = get_profile(db, user_id)
    if settings_data.notify_weekly_report is not None:
        profile.notify_weekly_report = settings_data.notify_weekly_report
    if settings_data.notify_gap_alerts is not None:
        profile.notify_gap_alerts = settings_data.notify_gap_alerts
    if settings_data.public_profile is not None:
        profile.public_profile = settings_data.public_profile
    if settings_data.show_raw_github_stats is not None:
        profile.show_raw_github_stats = settings_data.show_raw_github_stats
    
    db.commit()
    return get_profile(db, user_id)

def profile_to_response(profile: StudentProfile, user: User) -> ProfileResponse:
    role_name = profile.target_role.name if profile.target_role else None
    return ProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        email=user.email,
        name=profile.name,
        target_role_id=profile.target_role_id,
        target_role=role_name,
        github_username=profile.github_username,
        notify_weekly_report=profile.notify_weekly_report,
        notify_gap_alerts=profile.notify_gap_alerts,
        public_profile=profile.public_profile,
        show_raw_github_stats=profile.show_raw_github_stats,
    )
