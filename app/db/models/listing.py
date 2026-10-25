from datetime import datetime, timezone
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ListingModel(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    source_listing_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)

    make: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    trim: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model_year: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    mileage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    price_toman: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)
    price_mode: Mapped[str] = mapped_column(String(20), default="fixed", nullable=False)

    city: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    body_condition: Mapped[str | None] = mapped_column(String(100), nullable=True)
    engine_condition: Mapped[str | None] = mapped_column(String(100), nullable=True)
    gearbox: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)

    first_observed: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)
    last_observed: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("source_id", "source_listing_id", name="uq_source_listing"),
    )
