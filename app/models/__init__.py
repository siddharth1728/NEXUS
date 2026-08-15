from app.database.database import Base
from app.models.user import User, RefreshSession, UserSkill, Gap
from app.models.profile import StudentProfile
from app.models.taxonomy import TargetRole, Skill, TargetRoleSkill
from app.models.project import Project, RepositorySnapshot, Artifact, RawObservation, Evidence, EvidenceSkill
from app.models.action import ActionHistory, Recommendation
from app.models.claims import UserClaim
from app.models.ecosystem import (
    PermissionScope, RelationshipStatus,
    MentorRelationship, MentorNote, ReviewLink,
    Cohort, CohortMembership, Team, TeamMember, TeamProject, SharingAuditLog
)

# Ensure all models are imported here so Alembic can discover them
__all__ = [
    "Base", "User", "RefreshSession", "UserSkill", "Gap", "StudentProfile", "TargetRole", "Skill",
    "TargetRoleSkill", "Project", "RepositorySnapshot", "Artifact", "RawObservation", "Evidence",
    "EvidenceSkill", "ActionHistory", "Recommendation", "UserClaim",
    "PermissionScope", "RelationshipStatus", "MentorRelationship", "MentorNote", "ReviewLink",
    "Cohort", "CohortMembership", "Team", "TeamMember", "TeamProject", "SharingAuditLog"
]
