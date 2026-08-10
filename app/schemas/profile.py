from pydantic import BaseModel
from typing import Optional

class ProfileUpdate(BaseModel):
    target_role_id: Optional[int] = None
    github_username: Optional[str] = None

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    target_role_id: Optional[int] = None
    github_username: Optional[str] = None

    class Config:
        from_attributes = True
