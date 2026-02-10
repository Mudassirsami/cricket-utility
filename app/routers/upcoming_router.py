from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.security import require_manager_pin
from app.services.upcoming_service import UpcomingMatchService
from app.routers.notification_router import send_push_to_all
from app.schemas.upcoming import (
    CreateUpcomingMatchRequest, UpdateUpcomingMatchRequest,
    SubmitAvailabilityRequest, UpcomingMatchResponse,
    UpcomingMatchListItem, PlayerAvailabilityResponse,
)

router = APIRouter(prefix="/api/upcoming", tags=["Upcoming Matches"])


# ── PUBLIC ENDPOINTS ──────────────────────────────────────────

@router.get("", response_model=List[UpcomingMatchListItem])
async def list_upcoming_matches(db: AsyncSession = Depends(get_db)):
    return await UpcomingMatchService.list_matches(db)


@router.get("/{match_id}", response_model=UpcomingMatchResponse)
async def get_upcoming_match(match_id: str, db: AsyncSession = Depends(get_db)):
    return await UpcomingMatchService.get_match_with_availability(db, match_id)


@router.post("/{match_id}/availability", response_model=PlayerAvailabilityResponse)
async def submit_availability(
    match_id: str,
    req: SubmitAvailabilityRequest,
    db: AsyncSession = Depends(get_db),
):
    return await UpcomingMatchService.submit_availability(db, match_id, req)


# ── MANAGER-PROTECTED ENDPOINTS ───────────────────────────────

@router.post("", response_model=UpcomingMatchResponse, status_code=201)
async def create_upcoming_match(
    req: CreateUpcomingMatchRequest,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_manager_pin),
):
    match = await UpcomingMatchService.create_match(db, req)
    try:
        send_push_to_all(
            title="New Match Scheduled!",
            body=f"vs {req.opponent_name} — Check availability now",
            url=f"/upcoming/{match.id}",
        )
    except Exception:
        pass
    return await UpcomingMatchService.get_match_with_availability(db, match.id)


@router.put("/{match_id}", response_model=UpcomingMatchResponse)
async def update_upcoming_match(
    match_id: str,
    req: UpdateUpcomingMatchRequest,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_manager_pin),
):
    await UpcomingMatchService.update_match(db, match_id, req)
    return await UpcomingMatchService.get_match_with_availability(db, match_id)


@router.delete("/{match_id}", status_code=204)
async def delete_upcoming_match(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_manager_pin),
):
    await UpcomingMatchService.delete_match(db, match_id)
