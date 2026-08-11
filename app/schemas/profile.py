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

    model_config = ConfigDict(from_attributes=True)
