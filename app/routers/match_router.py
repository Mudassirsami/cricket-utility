from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.security import require_scorer_pin
from app.services.match_service import MatchService
from app.schemas.match import (
    CreateMatchRequest, SetTossRequest, StartInningsRequest,
    RecordBallRequest, ChangeBowlerRequest,
    MatchResponse, MatchListItem, FullScorecard, InningsResponse,
)
from typing import List

router = APIRouter(prefix="/api/matches", tags=["Matches"])


# ── PUBLIC ENDPOINTS ──────────────────────────────────────────

@router.get("", response_model=List[MatchListItem])
async def list_matches(db: AsyncSession = Depends(get_db)):
    return await MatchService.list_matches(db)


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(match_id: str, db: AsyncSession = Depends(get_db)):
    return await MatchService.get_match(db, match_id)


@router.get("/{match_id}/scorecard", response_model=FullScorecard)
async def get_scorecard(match_id: str, db: AsyncSession = Depends(get_db)):
    return await MatchService.get_scorecard(db, match_id)


# ── SCORER-PROTECTED ENDPOINTS ────────────────────────────────

@router.post("", response_model=MatchResponse, status_code=201)
async def create_match(
    req: CreateMatchRequest,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_scorer_pin),
):
    match = await MatchService.create_match(db, req)
    return await MatchService.get_match(db, match.id)


@router.post("/{match_id}/toss", response_model=MatchResponse)
async def set_toss(
    match_id: str,
    req: SetTossRequest,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_scorer_pin),
):
    await MatchService.set_toss(db, match_id, req)
    return await MatchService.get_match(db, match_id)


@router.post("/{match_id}/innings", response_model=InningsResponse, status_code=201)
async def start_innings(
    match_id: str,
    req: StartInningsRequest,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_scorer_pin),
):
    return await MatchService.start_innings(db, match_id, req)


@router.post("/{match_id}/ball")
async def record_ball(
    match_id: str,
    req: RecordBallRequest,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_scorer_pin),
):
    result = await MatchService.record_ball(db, match_id, req)
    match = await MatchService.get_match(db, match_id)
    return {
        "over_complete": result["over_complete"],
        "innings_ended": result["innings_ended"],
        "result_summary": result["result_summary"],
        "match": MatchResponse.model_validate(match),
    }


@router.post("/{match_id}/undo")
async def undo_last_ball(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_scorer_pin),
):
    result = await MatchService.undo_last_ball(db, match_id)
    match = await MatchService.get_match(db, match_id)
    return {
        "message": result["message"],
        "match": MatchResponse.model_validate(match),
    }


@router.post("/{match_id}/change-bowler", response_model=InningsResponse)
async def change_bowler(
    match_id: str,
    req: ChangeBowlerRequest,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_scorer_pin),
):
    return await MatchService.change_bowler(db, match_id, req)


@router.post("/{match_id}/swap-strike", response_model=InningsResponse)
async def swap_strike(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_scorer_pin),
):
    return await MatchService.swap_strike(db, match_id)


@router.post("/{match_id}/end-innings", response_model=MatchResponse)
async def end_innings(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_scorer_pin),
):
    return await MatchService.end_innings(db, match_id)


@router.post("/{match_id}/abandon", response_model=MatchResponse)
async def abandon_match(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_scorer_pin),
):
    return await MatchService.abandon_match(db, match_id)


@router.delete("/{match_id}", status_code=204)
async def delete_match(
    match_id: str,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_scorer_pin),
):
    await MatchService.delete_match(db, match_id)
