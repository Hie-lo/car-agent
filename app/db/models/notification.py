from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class NotificationRecord(Base):
    __tablename__ = "notification_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    watch_id: Mapped[str] = mapped_column(String(64), ForeignKey("watches.id", ondelete="CASCADE"), index=True, nullable=False)
    listing_id: Mapped[int] = mapped_column(Integer, ForeignKey("listings.id", ondelete="CASCADE"), index=True, nullable=False)
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    reason_codes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("watch_id", "listing_id", name="uq_watch_listing_notification"),
    )
