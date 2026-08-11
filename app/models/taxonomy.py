from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

class TargetRole(Base):
    __tablename__ = "target_roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    skills = relationship("TargetRoleSkill", back_populates="target_role", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)


class TargetRoleSkill(Base):
    __tablename__ = "target_role_skills"

    id = Column(Integer, primary_key=True, index=True)
    target_role_id = Column(Integer, ForeignKey("target_roles.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)
    importance_weight = Column(Float, nullable=False, default=1.0)
    minimum_expected_state = Column(String, nullable=False) # e.g. "DEVELOPING", "STRONG"

    target_role = relationship("TargetRole", back_populates="skills")
    skill = relationship("Skill")
