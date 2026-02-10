from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.models.finance import EntryType


class CreateFinancePeriodRequest(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=2000, le=2100)
    month: int = Field(..., ge=1, le=12)
    notes: Optional[str] = None


class UpdateFinancePeriodRequest(BaseModel):
    label: Optional[str] = Field(None, min_length=1, max_length=100)
    notes: Optional[str] = None


class CreateFinanceEntryRequest(BaseModel):
    entry_type: EntryType
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    amount: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)
    date: datetime


class UpdateFinanceEntryRequest(BaseModel):
    entry_type: Optional[EntryType] = None
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    amount: Optional[Decimal] = Field(None, gt=0, max_digits=12, decimal_places=2)
    date: Optional[datetime] = None


class FinanceEntryResponse(BaseModel):
    id: str
    period_id: str
    entry_type: EntryType
    category: str
    description: Optional[str]
    amount: Decimal
    date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PeriodSummary(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    remaining_balance: Decimal


class FinancePeriodResponse(BaseModel):
    id: str
    label: str
    year: int
    month: int
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    entries: List[FinanceEntryResponse] = []
    summary: Optional[PeriodSummary] = None

    class Config:
        from_attributes = True


class FinancePeriodListItem(BaseModel):
    id: str
    label: str
    year: int
    month: int
    created_at: datetime
    summary: Optional[PeriodSummary] = None

    class Config:
        from_attributes = True


class OverallFinanceSummary(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    remaining_balance: Decimal
    periods: List[FinancePeriodListItem]
