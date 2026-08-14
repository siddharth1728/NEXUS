from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database.database import Base

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    target_role_id = Column(Integer, ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True, index=True)
    github_username = Column(String, nullable=True)
    name = Column(String, nullable=True)

    # Preferences
    notify_weekly_report = Column(Boolean, default=True, nullable=False)
    notify_gap_alerts = Column(Boolean, default=True, nullable=False)
    public_profile = Column(Boolean, default=False, nullable=False)
    show_raw_github_stats = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="profile")
    target_role = relationship("TargetRole")
