import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base

class ActionHistoryStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    DISMISSED = "DISMISSED"

class ActionHistory(Base):
    __tablename__ = "action_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action_key = Column(String, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    status = Column(Enum(ActionHistoryStatus, native_enum=False, length=20), nullable=False)
    
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")
    project = relationship("Project")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    gap_id = Column(Integer, ForeignKey("gaps.id", ondelete="CASCADE"), nullable=False)
    action_key = Column(String, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    effort = Column(Integer, nullable=False) # 1=LOW, 2=MEDIUM, 3=HIGH
    priority_score = Column(Float, nullable=False)
    
    calculation_version = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")
    gap = relationship("Gap")
    project = relationship("Project")
