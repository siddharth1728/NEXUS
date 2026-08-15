from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Enum, Float, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database.database import Base

class SnapshotStatus(str, enum.Enum):
    PENDING = "PENDING"
    ANALYZING = "ANALYZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    github_repo_id = Column(Integer, nullable=False, index=True)
    name = Column(String, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    
    user = relationship("User", back_populates="projects")
    snapshots = relationship("RepositorySnapshot", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint('user_id', 'github_repo_id', name='uq_user_github_repo'),
    )

class RepositorySnapshot(Base):
    __tablename__ = "repository_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    commit_sha = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())
    analysis_started_at = Column(DateTime(timezone=True), nullable=True)
    analysis_completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(SnapshotStatus, native_enum=False, length=20), default=SnapshotStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)

    project = relationship("Project", back_populates="snapshots")
    artifacts = relationship("Artifact", back_populates="snapshot", cascade="all, delete-orphan")

class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_id = Column(Integer, ForeignKey("repository_snapshots.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)

    snapshot = relationship("RepositorySnapshot", back_populates="artifacts")
    observations = relationship("RawObservation", back_populates="artifact", cascade="all, delete-orphan")

class RawObservation(Base):
    __tablename__ = "raw_observations"

    id = Column(Integer, primary_key=True, index=True)
    artifact_id = Column(Integer, ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False, index=True)
    observation_text = Column(String, nullable=False)
    line_numbers = Column(String, nullable=True)

    artifact = relationship("Artifact", back_populates="observations")
    evidence = relationship("Evidence", back_populates="raw_observation", cascade="all, delete-orphan", uselist=False)

class EvidenceType(str, enum.Enum):
    IMPLEMENTATION = "IMPLEMENTATION"
    TESTING = "TESTING"
    CONFIGURATION = "CONFIGURATION"
    CI_CD = "CI_CD"
    DATABASE = "DATABASE"
    AUTHENTICATION = "AUTHENTICATION"
    API = "API"
    ARCHITECTURE = "ARCHITECTURE"
    DOCUMENTATION = "DOCUMENTATION"
    CONTAINERIZATION = "CONTAINERIZATION"
    DEPENDENCY = "DEPENDENCY"
    OBSERVABILITY = "OBSERVABILITY"

class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    raw_observation_id = Column(Integer, ForeignKey("raw_observations.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(Enum(EvidenceType, native_enum=False, length=50), nullable=False)
    quality_score = Column(Float, nullable=False)
    freshness_weight = Column(Float, nullable=False)
    source_reference = Column(String, nullable=True)

    raw_observation = relationship("RawObservation", back_populates="evidence")
    skills = relationship("EvidenceSkill", back_populates="evidence", cascade="all, delete-orphan")

class EvidenceSkill(Base):
    __tablename__ = "evidence_skills"

    id = Column(Integer, primary_key=True, index=True)
    evidence_id = Column(Integer, ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)

    evidence = relationship("Evidence", back_populates="skills")
    skill = relationship("Skill")

    __table_args__ = (
        UniqueConstraint('evidence_id', 'skill_id', name='uq_evidence_skill'),
    )
