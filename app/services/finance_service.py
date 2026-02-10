from typing import List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.finance import FinancePeriod, FinanceEntry, EntryType
from app.schemas.finance import (
    CreateFinancePeriodRequest, UpdateFinancePeriodRequest,
    CreateFinanceEntryRequest, UpdateFinanceEntryRequest,
    PeriodSummary, FinancePeriodResponse, FinancePeriodListItem,
    OverallFinanceSummary,
)


class FinanceService:

    @staticmethod
    async def create_period(db: AsyncSession, req: CreateFinancePeriodRequest) -> FinancePeriod:
        stmt = select(FinancePeriod).where(
            FinancePeriod.year == req.year,
            FinancePeriod.month == req.month,
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="A finance period for this month/year already exists.")

        period = FinancePeriod(
            label=req.label.strip(),
            year=req.year,
            month=req.month,
            notes=req.notes,
        )
        db.add(period)
        await db.commit()
        await db.refresh(period)
        return period

    @staticmethod
    async def update_period(db: AsyncSession, period_id: str, req: UpdateFinancePeriodRequest) -> FinancePeriod:
        period = await FinanceService._get_period(db, period_id)
        if req.label is not None:
            period.label = req.label.strip()
        if req.notes is not None:
            period.notes = req.notes
        await db.commit()
        await db.refresh(period)
        return period

    @staticmethod
    async def delete_period(db: AsyncSession, period_id: str) -> None:
        period = await FinanceService._get_period(db, period_id)
        await db.delete(period)
        await db.commit()

    @staticmethod
    async def _get_period(db: AsyncSession, period_id: str) -> FinancePeriod:
        stmt = (
            select(FinancePeriod)
            .options(selectinload(FinancePeriod.entries))
            .where(FinancePeriod.id == period_id)
        )
        result = await db.execute(stmt)
        period = result.scalar_one_or_none()
        if not period:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finance period not found.")
        return period

    @staticmethod
    async def get_period_with_summary(db: AsyncSession, period_id: str) -> FinancePeriodResponse:
        period = await FinanceService._get_period(db, period_id)
        summary = FinanceService._calculate_period_summary(period.entries)
        resp = FinancePeriodResponse.model_validate(period)
        resp.summary = summary
        return resp

    @staticmethod
    async def list_periods(db: AsyncSession) -> List[FinancePeriodListItem]:
        stmt = (
            select(FinancePeriod)
            .options(selectinload(FinancePeriod.entries))
            .order_by(FinancePeriod.year.desc(), FinancePeriod.month.desc())
        )
        result = await db.execute(stmt)
        periods = result.scalars().all()
        items = []
        for p in periods:
            summary = FinanceService._calculate_period_summary(p.entries)
            item = FinancePeriodListItem.model_validate(p)
            item.summary = summary
            items.append(item)
        return items

    @staticmethod
    async def get_overall_summary(db: AsyncSession) -> OverallFinanceSummary:
        periods = await FinanceService.list_periods(db)
        total_income = Decimal("0.00")
        total_expense = Decimal("0.00")
        for p in periods:
            if p.summary:
                total_income += p.summary.total_income
                total_expense += p.summary.total_expense
        return OverallFinanceSummary(
            total_income=total_income,
            total_expense=total_expense,
            remaining_balance=total_income - total_expense,
            periods=periods,
        )

    @staticmethod
    def _calculate_period_summary(entries: List[FinanceEntry]) -> PeriodSummary:
        total_income = Decimal("0.00")
        total_expense = Decimal("0.00")
        for e in entries:
            if e.entry_type == EntryType.INCOME:
                total_income += e.amount
            else:
                total_expense += e.amount
        return PeriodSummary(
            total_income=total_income,
            total_expense=total_expense,
            remaining_balance=total_income - total_expense,
        )

    @staticmethod
    async def add_entry(db: AsyncSession, period_id: str, req: CreateFinanceEntryRequest) -> FinanceEntry:
        await FinanceService._get_period(db, period_id)
        entry = FinanceEntry(
            period_id=period_id,
            entry_type=req.entry_type,
            category=req.category.strip(),
            description=req.description,
            amount=req.amount,
            date=req.date,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    @staticmethod
    async def update_entry(db: AsyncSession, entry_id: str, req: UpdateFinanceEntryRequest) -> FinanceEntry:
        stmt = select(FinanceEntry).where(FinanceEntry.id == entry_id)
        result = await db.execute(stmt)
        entry = result.scalar_one_or_none()
        if not entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finance entry not found.")
        if req.entry_type is not None:
            entry.entry_type = req.entry_type
        if req.category is not None:
            entry.category = req.category.strip()
        if req.description is not None:
            entry.description = req.description
        if req.amount is not None:
            entry.amount = req.amount
        if req.date is not None:
            entry.date = req.date
        await db.commit()
        await db.refresh(entry)
        return entry

    @staticmethod
    async def delete_entry(db: AsyncSession, entry_id: str) -> None:
        stmt = select(FinanceEntry).where(FinanceEntry.id == entry_id)
        result = await db.execute(stmt)
        entry = result.scalar_one_or_none()
        if not entry:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finance entry not found.")
        await db.delete(entry)
        await db.commit()
