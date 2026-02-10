from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.upcoming import UpcomingMatch, PlayerAvailability, AvailabilityStatus
from app.schemas.upcoming import (
    CreateUpcomingMatchRequest, UpdateUpcomingMatchRequest,
    SubmitAvailabilityRequest, AvailabilitySummary,
    PlayerAvailabilityResponse, UpcomingMatchResponse,
)


class UpcomingMatchService:

    @staticmethod
    async def create_match(db: AsyncSession, req: CreateUpcomingMatchRequest) -> UpcomingMatch:
        match = UpcomingMatch(
            opponent_name=req.opponent_name.strip(),
            match_date=req.match_date,
            venue=req.venue.strip() if req.venue else None,
            overs=req.overs,
            notes=req.notes,
        )
        db.add(match)
        await db.commit()
        await db.refresh(match)
        return match

    @staticmethod
    async def update_match(db: AsyncSession, match_id: str, req: UpdateUpcomingMatchRequest) -> UpcomingMatch:
        match = await UpcomingMatchService.get_match(db, match_id)
        if req.opponent_name is not None:
            match.opponent_name = req.opponent_name.strip()
        if req.match_date is not None:
            match.match_date = req.match_date
        if req.venue is not None:
            match.venue = req.venue.strip()
        if req.overs is not None:
            match.overs = req.overs
        if req.notes is not None:
            match.notes = req.notes
        await db.commit()
        await db.refresh(match)
        return match

    @staticmethod
    async def delete_match(db: AsyncSession, match_id: str) -> None:
        match = await UpcomingMatchService.get_match(db, match_id)
        await db.delete(match)
        await db.commit()

    @staticmethod
    async def get_match(db: AsyncSession, match_id: str) -> UpcomingMatch:
        stmt = (
            select(UpcomingMatch)
            .options(selectinload(UpcomingMatch.availabilities))
            .where(UpcomingMatch.id == match_id)
        )
        result = await db.execute(stmt)
        match = result.scalar_one_or_none()
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upcoming match not found.")
        return match

    @staticmethod
    async def list_matches(db: AsyncSession) -> List[UpcomingMatch]:
        stmt = select(UpcomingMatch).order_by(UpcomingMatch.match_date.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_match_with_availability(db: AsyncSession, match_id: str) -> UpcomingMatchResponse:
        match = await UpcomingMatchService.get_match(db, match_id)
        summary = UpcomingMatchService._build_summary(match.availabilities)
        resp = UpcomingMatchResponse.model_validate(match)
        resp.availability_summary = summary
        return resp

    @staticmethod
    def _build_summary(availabilities: List[PlayerAvailability]) -> AvailabilitySummary:
        available = 0
        not_available = 0
        maybe = 0
        players = []
        for a in availabilities:
            if a.status == AvailabilityStatus.AVAILABLE:
                available += 1
            elif a.status == AvailabilityStatus.NOT_AVAILABLE:
                not_available += 1
            elif a.status == AvailabilityStatus.MAYBE:
                maybe += 1
            players.append(PlayerAvailabilityResponse.model_validate(a))
        return AvailabilitySummary(
            total_available=available,
            total_not_available=not_available,
            total_maybe=maybe,
            players=players,
        )

    @staticmethod
    async def submit_availability(
        db: AsyncSession, match_id: str, req: SubmitAvailabilityRequest
    ) -> PlayerAvailability:
        await UpcomingMatchService.get_match(db, match_id)

        stmt = select(PlayerAvailability).where(
            PlayerAvailability.upcoming_match_id == match_id,
            PlayerAvailability.device_fingerprint == req.device_fingerprint,
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.player_name = req.player_name.strip()
            existing.status = req.status
            await db.commit()
            await db.refresh(existing)
            return existing

        availability = PlayerAvailability(
            upcoming_match_id=match_id,
            player_name=req.player_name.strip(),
            status=req.status,
            device_fingerprint=req.device_fingerprint,
        )
        db.add(availability)
        await db.commit()
        await db.refresh(availability)
        return availability
