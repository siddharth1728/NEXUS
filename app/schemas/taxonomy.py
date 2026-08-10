from pydantic import BaseModel
from typing import Optional

class TargetRoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class SkillResponse(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None

    class Config:
        from_attributes = True
