import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from app.database.database import Base

class PermissionScope(str, enum.Enum):
    PROFILE = "PROFILE"
    PROJECTS = "PROJECTS"
    PROOF = "PROOF"
    JOURNEY = "JOURNEY"
    ATLAS = "ATLAS"
    QUESTS = "QUESTS"
    LAB = "LAB"
    CLAIMS = "CLAIMS"

class RelationshipStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"

class MentorRelationship(Base):
    __tablename__ = "mentor_relationships"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mentor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    invite_token = Column(String, unique=True, index=True, nullable=False)
    mentor_email = Column(String, nullable=True)
    status = Column(Enum(RelationshipStatus, native_enum=False, length=20), default=RelationshipStatus.PENDING, nullable=False)
    permissions = Column(Text, nullable=False, default='["PROFILE", "PROJECTS", "PROOF", "JOURNEY", "QUESTS"]')  # JSON list of PermissionScope strings
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)

    student = relationship("User", foreign_keys=[student_id])
    mentor = relationship("User", foreign_keys=[mentor_id])
    notes = relationship("MentorNote", back_populates="mentor_rel", cascade="all, delete-orphan")

class MentorNote(Base):
    __tablename__ = "mentor_notes"

    id = Column(Integer, primary_key=True, index=True)
    relationship_id = Column(Integer, ForeignKey("mentor_relationships.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    note_text = Column(Text, nullable=False)
    recommended_quest_id = Column(Integer, nullable=True)
    recommended_concept_key = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    mentor_rel = relationship("MentorRelationship", back_populates="notes")
    author = relationship("User", foreign_keys=[author_id])
    student = relationship("User", foreign_keys=[student_id])

class ReviewLink(Base):
    __tablename__ = "review_links"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    label = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("User", foreign_keys=[student_id])
    project = relationship("Project", foreign_keys=[project_id])

class Cohort(Base):
    __tablename__ = "cohorts"

    id = Column(Integer, primary_key=True, index=True)
    educator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    course_code = Column(String, nullable=False)
    invite_code = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    educator = relationship("User", foreign_keys=[educator_id])
    memberships = relationship("CohortMembership", back_populates="cohort", cascade="all, delete-orphan")

class CohortMembership(Base):
    __tablename__ = "cohort_memberships"

    id = Column(Integer, primary_key=True, index=True)
    cohort_id = Column(Integer, ForeignKey("cohorts.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    cohort = relationship("Cohort", back_populates="memberships")
    student = relationship("User", foreign_keys=[student_id])

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    invite_code = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    creator = relationship("User", foreign_keys=[creator_id])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    projects = relationship("TeamProject", back_populates="team", cascade="all, delete-orphan")

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, default="MEMBER", nullable=False)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    team = relationship("Team", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])

class TeamProject(Base):
    __tablename__ = "team_projects"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    shared_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    team = relationship("Team", back_populates="projects")
    project = relationship("Project", foreign_keys=[project_id])

class SharingAuditLog(Base):
    __tablename__ = "sharing_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    resource_owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String, nullable=False)  # e.g., "VIEW_PROFILE", "VIEW_PROOF", "VIEW_REVIEW_LINK", "REVOKE_MENTOR"
    target_type = Column(String, nullable=False)  # e.g., "MENTOR", "REVIEW_LINK", "PUBLIC_PROFILE", "COHORT"
    target_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    resource_owner = relationship("User", foreign_keys=[resource_owner_id])
    actor = relationship("User", foreign_keys=[actor_id])
