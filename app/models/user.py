from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, Float
from sqlalchemy.orm import relationship
from app.database.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    refresh_sessions = relationship("RefreshSession", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    user_skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")

class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="refresh_sessions")

import enum
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func

class SkillState(str, enum.Enum):
    MISSING = "MISSING"
    WEAK = "WEAK"
    DEVELOPING = "DEVELOPING"
    STRONG = "STRONG"

class UserSkill(Base):
    __tablename__ = "user_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    state = Column(Enum(SkillState, native_enum=False, length=20), nullable=False)
    
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    calculation_version = Column(String, nullable=False)

    user = relationship("User", back_populates="user_skills")
    skill = relationship("Skill")

    __table_args__ = (
        UniqueConstraint('user_id', 'skill_id', name='uq_user_skill'),
    )

class Gap(Base):
    __tablename__ = "gaps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    actual_state = Column(String, nullable=False)
    required_state = Column(String, nullable=False)
    state_distance = Column(Integer, nullable=False)
    importance_weight = Column(Float, nullable=False)
    severity = Column(Float, nullable=False)

    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    calculation_version = Column(String, nullable=False)

    user = relationship("User")
    skill = relationship("Skill")

    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_gap"),
    )
