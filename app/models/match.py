import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Enum, Float
)
from sqlalchemy.orm import relationship

from app.database import Base


class MatchStatus(str, PyEnum):
    TOSS = "toss"
    IN_PROGRESS = "in_progress"
    INNINGS_BREAK = "innings_break"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InningsStatus(str, PyEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class DismissalType(str, PyEnum):
    BOWLED = "bowled"
    CAUGHT = "caught"
    LBW = "lbw"
    RUN_OUT = "run_out"
    STUMPED = "stumped"
    HIT_WICKET = "hit_wicket"
    RETIRED_HURT = "retired_hurt"
    OBSTRUCTING = "obstructing_the_field"
    TIMED_OUT = "timed_out"
    HANDLED_BALL = "handled_the_ball"


class ExtraType(str, PyEnum):
    NONE = "none"
    WIDE = "wide"
    NO_BALL = "no_ball"
    BYE = "bye"
    LEG_BYE = "leg_bye"
    PENALTY = "penalty"


class Match(Base):
    __tablename__ = "matches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_a_name = Column(String(100), nullable=False)
    team_b_name = Column(String(100), nullable=False)
    total_overs = Column(Integer, nullable=False)
    venue = Column(String(200), nullable=True)
    toss_winner = Column(String(100), nullable=True)
    toss_decision = Column(String(10), nullable=True)  # bat / bowl
    status = Column(Enum(MatchStatus), default=MatchStatus.TOSS, nullable=False)
    result_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    innings = relationship("Innings", back_populates="match", cascade="all, delete-orphan", order_by="Innings.innings_number")


class Innings(Base):
    __tablename__ = "innings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String(36), ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    innings_number = Column(Integer, nullable=False)  # 1 or 2
    batting_team = Column(String(100), nullable=False)
    bowling_team = Column(String(100), nullable=False)
    total_runs = Column(Integer, default=0, nullable=False)
    total_wickets = Column(Integer, default=0, nullable=False)
    total_overs_bowled = Column(Float, default=0.0, nullable=False)
    extras_wides = Column(Integer, default=0, nullable=False)
    extras_no_balls = Column(Integer, default=0, nullable=False)
    extras_byes = Column(Integer, default=0, nullable=False)
    extras_leg_byes = Column(Integer, default=0, nullable=False)
    extras_penalties = Column(Integer, default=0, nullable=False)
    target = Column(Integer, nullable=True)
    status = Column(Enum(InningsStatus), default=InningsStatus.NOT_STARTED, nullable=False)
    current_over = Column(Integer, default=0, nullable=False)
    current_ball = Column(Integer, default=0, nullable=False)
    striker_name = Column(String(100), nullable=True)
    non_striker_name = Column(String(100), nullable=True)
    current_bowler_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    match = relationship("Match", back_populates="innings")
    balls = relationship("BallEvent", back_populates="innings", cascade="all, delete-orphan", order_by="BallEvent.sequence_number")


class BallEvent(Base):
    __tablename__ = "ball_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    innings_id = Column(String(36), ForeignKey("innings.id", ondelete="CASCADE"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    over_number = Column(Integer, nullable=False)
    ball_number = Column(Integer, nullable=False)
    bowler_name = Column(String(100), nullable=False)
    batsman_name = Column(String(100), nullable=False)
    non_striker_name = Column(String(100), nullable=False)
    runs_scored = Column(Integer, default=0, nullable=False)
    is_boundary_four = Column(Boolean, default=False, nullable=False)
    is_boundary_six = Column(Boolean, default=False, nullable=False)
    extra_type = Column(Enum(ExtraType), default=ExtraType.NONE, nullable=False)
    extra_runs = Column(Integer, default=0, nullable=False)
    is_wicket = Column(Boolean, default=False, nullable=False)
    dismissal_type = Column(Enum(DismissalType), nullable=True)
    dismissed_batsman = Column(String(100), nullable=True)
    fielder_name = Column(String(100), nullable=True)
    is_legal_delivery = Column(Boolean, default=True, nullable=False)
    is_undone = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    innings = relationship("Innings", back_populates="balls")
