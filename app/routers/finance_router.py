from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.security import require_manager_pin
from app.services.finance_service import FinanceService
from app.schemas.finance import (
    CreateFinancePeriodRequest, UpdateFinancePeriodRequest,
    CreateFinanceEntryRequest, UpdateFinanceEntryRequest,
    FinancePeriodResponse, FinancePeriodListItem,
    FinanceEntryResponse, OverallFinanceSummary,
)

router = APIRouter(prefix="/api/finance", tags=["Finance"])


# ── PUBLIC ENDPOINTS ──────────────────────────────────────────

@router.get("/summary", response_model=OverallFinanceSummary)
async def get_overall_summary(db: AsyncSession = Depends(get_db)):
    return await FinanceService.get_overall_summary(db)


@router.get("/periods", response_model=List[FinancePeriodListItem])
async def list_periods(db: AsyncSession = Depends(get_db)):
    return await FinanceService.list_periods(db)


@router.get("/periods/{period_id}", response_model=FinancePeriodResponse)
async def get_period(period_id: str, db: AsyncSession = Depends(get_db)):
    return await FinanceService.get_period_with_summary(db, period_id)


# ── MANAGER-PROTECTED ENDPOINTS ───────────────────────────────

@router.post("/periods", response_model=FinancePeriodResponse, status_code=201)
async def create_period(
    req: CreateFinancePeriodRequest,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_manager_pin),
):
    period = await FinanceService.create_period(db, req)
    return await FinanceService.get_period_with_summary(db, period.id)


@router.put("/periods/{period_id}", response_model=FinancePeriodResponse)
async def update_period(
    period_id: str,
    req: UpdateFinancePeriodRequest,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_manager_pin),
):
    await FinanceService.update_period(db, period_id, req)
    return await FinanceService.get_period_with_summary(db, period_id)


@router.delete("/periods/{period_id}", status_code=204)
async def delete_period(
    period_id: str,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_manager_pin),
):
    await FinanceService.delete_period(db, period_id)


@router.post("/periods/{period_id}/entries", response_model=FinanceEntryResponse, status_code=201)
async def add_entry(
    period_id: str,
    req: CreateFinanceEntryRequest,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_manager_pin),
):
    return await FinanceService.add_entry(db, period_id, req)


@router.put("/entries/{entry_id}", response_model=FinanceEntryResponse)
async def update_entry(
    entry_id: str,
    req: UpdateFinanceEntryRequest,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_manager_pin),
):
    return await FinanceService.update_entry(db, entry_id, req)


@router.delete("/entries/{entry_id}", status_code=204)
async def delete_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    _pin=Depends(require_manager_pin),
):
    await FinanceService.delete_entry(db, entry_id)
