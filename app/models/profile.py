from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database.database import Base

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    target_role_id = Column(Integer, ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True, index=True)
    github_username = Column(String, nullable=True)

    user = relationship("User", back_populates="profile")
    target_role = relationship("TargetRole")
