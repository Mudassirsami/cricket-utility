from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.upcoming import AvailabilityStatus


class CreateUpcomingMatchRequest(BaseModel):
    opponent_name: str = Field(..., min_length=1, max_length=100)
    match_date: datetime
    venue: Optional[str] = Field(None, max_length=200)
    overs: Optional[int] = Field(None, gt=0, le=50)
    notes: Optional[str] = None


class UpdateUpcomingMatchRequest(BaseModel):
    opponent_name: Optional[str] = Field(None, min_length=1, max_length=100)
    match_date: Optional[datetime] = None
    venue: Optional[str] = Field(None, max_length=200)
    overs: Optional[int] = Field(None, gt=0, le=50)
    notes: Optional[str] = None


class SubmitAvailabilityRequest(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=100)
    status: AvailabilityStatus
    device_fingerprint: str = Field(..., min_length=1, max_length=255)


class PlayerAvailabilityResponse(BaseModel):
    id: str
    player_name: str
    status: AvailabilityStatus
    created_at: datetime

    class Config:
        from_attributes = True


class AvailabilitySummary(BaseModel):
    total_available: int
    total_not_available: int
    total_maybe: int
    players: List[PlayerAvailabilityResponse]


class UpcomingMatchResponse(BaseModel):
    id: str
    opponent_name: str
    match_date: datetime
    venue: Optional[str]
    overs: Optional[int]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    availability_summary: Optional[AvailabilitySummary] = None

    class Config:
        from_attributes = True


class UpcomingMatchListItem(BaseModel):
    id: str
    opponent_name: str
    match_date: datetime
    venue: Optional[str]
    overs: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
