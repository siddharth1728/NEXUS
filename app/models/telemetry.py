from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base

class ProductEvent(Base):
    """
    Lightweight event model for product telemetry.
    DO NOT store PII, raw source code, or secrets in context_data.
    """
    __tablename__ = "product_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    context_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    user = relationship("User")

class ProductFeedback(Base):
    """
    Contextual user feedback model.
    """
    __tablename__ = "product_feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_context = Column(String(100), nullable=False, index=True)
    is_helpful = Column(Boolean, nullable=False)
    reason = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User")
