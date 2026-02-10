import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship

from app.database import Base


class AvailabilityStatus(str, PyEnum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"
    MAYBE = "maybe"


class UpcomingMatch(Base):
    __tablename__ = "upcoming_matches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    opponent_name = Column(String(100), nullable=False)
    match_date = Column(DateTime, nullable=False)
    venue = Column(String(200), nullable=True)
    overs = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    availabilities = relationship(
        "PlayerAvailability",
        back_populates="upcoming_match",
        cascade="all, delete-orphan",
    )


class PlayerAvailability(Base):
    __tablename__ = "player_availabilities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    upcoming_match_id = Column(
        String(36),
        ForeignKey("upcoming_matches.id", ondelete="CASCADE"),
        nullable=False,
    )
    player_name = Column(String(100), nullable=False)
    status = Column(Enum(AvailabilityStatus), nullable=False)
    device_fingerprint = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    upcoming_match = relationship("UpcomingMatch", back_populates="availabilities")
