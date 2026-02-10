import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, Text, Numeric
from sqlalchemy.orm import relationship

from app.database import Base


class EntryType(str, PyEnum):
    INCOME = "income"
    EXPENSE = "expense"


class FinancePeriod(Base):
    __tablename__ = "finance_periods"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    label = Column(String(100), nullable=False)  # e.g. "January 2026"
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    entries = relationship(
        "FinanceEntry",
        back_populates="period",
        cascade="all, delete-orphan",
    )


class FinanceEntry(Base):
    __tablename__ = "finance_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    period_id = Column(
        String(36),
        ForeignKey("finance_periods.id", ondelete="CASCADE"),
        nullable=False,
    )
    entry_type = Column(Enum(EntryType), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    period = relationship("FinancePeriod", back_populates="entries")
