from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.match import MatchStatus, InningsStatus, DismissalType, ExtraType


class CreateMatchRequest(BaseModel):
    team_a_name: str = Field(..., min_length=1, max_length=100)
    team_b_name: str = Field(..., min_length=1, max_length=100)
    total_overs: int = Field(..., gt=0, le=50)
    venue: Optional[str] = Field(None, max_length=200)


class SetTossRequest(BaseModel):
    toss_winner: str = Field(..., min_length=1, max_length=100)
    toss_decision: str = Field(..., pattern="^(bat|bowl)$")


class StartInningsRequest(BaseModel):
    batting_team: str = Field(..., min_length=1, max_length=100)
    bowling_team: str = Field(..., min_length=1, max_length=100)
    striker_name: str = Field(..., min_length=1, max_length=100)
    non_striker_name: str = Field(..., min_length=1, max_length=100)
    bowler_name: str = Field(..., min_length=1, max_length=100)


class RecordBallRequest(BaseModel):
    runs_scored: int = Field(0, ge=0, le=7)
    is_boundary_four: bool = False
    is_boundary_six: bool = False
    extra_type: ExtraType = ExtraType.NONE
    extra_runs: int = Field(0, ge=0, le=7)
    is_wicket: bool = False
    dismissal_type: Optional[DismissalType] = None
    dismissed_batsman: Optional[str] = Field(None, max_length=100)
    fielder_name: Optional[str] = Field(None, max_length=100)
    new_batsman_name: Optional[str] = Field(None, max_length=100)


class ChangeBowlerRequest(BaseModel):
    bowler_name: str = Field(..., min_length=1, max_length=100)


class ChangeStrikeRequest(BaseModel):
    pass


class BallEventResponse(BaseModel):
    id: str
    sequence_number: int
    over_number: int
    ball_number: int
    bowler_name: str
    batsman_name: str
    non_striker_name: str
    runs_scored: int
    is_boundary_four: bool
    is_boundary_six: bool
    extra_type: ExtraType
    extra_runs: int
    is_wicket: bool
    dismissal_type: Optional[DismissalType]
    dismissed_batsman: Optional[str]
    fielder_name: Optional[str]
    is_legal_delivery: bool
    created_at: datetime

    class Config:
        from_attributes = True


class InningsResponse(BaseModel):
    id: str
    innings_number: int
    batting_team: str
    bowling_team: str
    total_runs: int
    total_wickets: int
    total_overs_bowled: float
    extras_wides: int
    extras_no_balls: int
    extras_byes: int
    extras_leg_byes: int
    extras_penalties: int
    target: Optional[int]
    status: InningsStatus
    current_over: int
    current_ball: int
    striker_name: Optional[str]
    non_striker_name: Optional[str]
    current_bowler_name: Optional[str]
    balls: List[BallEventResponse] = []

    class Config:
        from_attributes = True


class MatchResponse(BaseModel):
    id: str
    team_a_name: str
    team_b_name: str
    total_overs: int
    venue: Optional[str]
    toss_winner: Optional[str]
    toss_decision: Optional[str]
    status: MatchStatus
    result_summary: Optional[str]
    created_at: datetime
    updated_at: datetime
    innings: List[InningsResponse] = []

    class Config:
        from_attributes = True


class MatchListItem(BaseModel):
    id: str
    team_a_name: str
    team_b_name: str
    total_overs: int
    venue: Optional[str]
    status: MatchStatus
    result_summary: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class BatsmanStats(BaseModel):
    name: str
    runs: int
    balls_faced: int
    fours: int
    sixes: int
    strike_rate: float
    how_out: Optional[str]
    bowler: Optional[str]


class BowlerStats(BaseModel):
    name: str
    overs: str
    maidens: int
    runs_conceded: int
    wickets: int
    economy: float
    wides: int
    no_balls: int


class InningsScorecard(BaseModel):
    innings_number: int
    batting_team: str
    bowling_team: str
    total_runs: int
    total_wickets: int
    total_overs: str
    extras: dict
    batsmen: List[BatsmanStats]
    bowlers: List[BowlerStats]
    fall_of_wickets: List[dict]


class FullScorecard(BaseModel):
    match: MatchListItem
    innings: List[InningsScorecard]
