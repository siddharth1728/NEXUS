from pydantic import BaseModel, ConfigDict
from typing import Optional

class ProfileUpdate(BaseModel):
    target_role_id: Optional[int] = None
    target_role: Optional[str] = None
    github_username: Optional[str] = None
    name: Optional[str] = None

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    email: str
    name: Optional[str] = None
    target_role_id: Optional[int] = None
    target_role: Optional[str] = None
    github_username: Optional[str] = None
    
    notify_weekly_report: bool = True
    notify_gap_alerts: bool = True
    public_profile: bool = False
    show_raw_github_stats: bool = True

    model_config = ConfigDict(from_attributes=True)

class SettingsUpdate(BaseModel):
    notify_weekly_report: Optional[bool] = None
    notify_gap_alerts: Optional[bool] = None
    public_profile: Optional[bool] = None
    show_raw_github_stats: Optional[bool] = None
