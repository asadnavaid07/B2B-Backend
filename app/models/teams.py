from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("teams.id"), nullable=True)  # For sub-divisions
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    sub_teams = relationship("Team", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Team", remote_side=[id], back_populates="sub_teams")

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=False)
    bio = Column(Text, nullable=True)
    image = Column(String(255), nullable=True)  # Stores file path or URL
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    team = relationship("Team", back_populates="members")