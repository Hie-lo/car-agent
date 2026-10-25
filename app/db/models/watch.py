from datetime import datetime, timezone
from typing import Any
from sqlalchemy import BigInteger, DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Watch(Base):
    __tablename__ = "watches"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    trim: Mapped[str | None] = mapped_column(String(100), nullable=True)
    year_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_min: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    budget_max: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    budget_mode: Mapped[str] = mapped_column(String(20), default="strict", nullable=False)
    max_overage_pct: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    mileage_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hard_constraints: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
