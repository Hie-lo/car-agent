from datetime import datetime, timezone
from typing import Any
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import CreditLedger, JobQueue, ListingModel, NotificationRecord, User, Watch
from app.domain.enums import SourceStatus
from app.sources.registry import SourceRegistryEntry


async def get_system_metrics(session: AsyncSession) -> dict[str, Any]:
    """
    Collects real-time operational metrics for admin dashboard and monitoring:
    - Active watches, users, total listings
    - Queue lag & worker status (pending, processing, failed)
    - Notifications sent today
    Adheres to Section 11 & Section 13 of AGENTS.md.
    """
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)

    # 1. User & Watch stats
    total_users = (await session.execute(select(func.count(User.id)))).scalar() or 0
    active_watches = (await session.execute(
        select(func.count(Watch.id)).where(Watch.status == "active")
    )).scalar() or 0

    # 2. Listings stats
    total_listings = (await session.execute(select(func.count(ListingModel.id)))).scalar() or 0

    # 3. Queue lag stats
    pending_jobs = (await session.execute(
        select(func.count(JobQueue.id)).where(JobQueue.status == "pending")
    )).scalar() or 0

    processing_jobs = (await session.execute(
        select(func.count(JobQueue.id)).where(JobQueue.status == "processing")
    )).scalar() or 0

    failed_jobs = (await session.execute(
        select(func.count(JobQueue.id)).where(JobQueue.status == "failed")
    )).scalar() or 0

    # 4. Notifications sent today
    notifications_today = (await session.execute(
        select(func.count(NotificationRecord.id)).where(NotificationRecord.sent_at >= today_start)
    )).scalar() or 0

    return {
        "timestamp": now.isoformat(),
        "users": {
            "total": total_users,
        },
        "watches": {
            "active": active_watches,
        },
        "listings": {
            "total": total_listings,
        },
        "queue": {
            "pending": pending_jobs,
            "processing": processing_jobs,
            "failed": failed_jobs,
            "is_healthy": failed_jobs == 0 and pending_jobs < 1000,
        },
        "notifications": {
            "sent_today": notifications_today,
        },
        "sources": {
            "divar": {"status": SourceStatus.APPROVED.value},
            "bama": {"status": SourceStatus.BLOCKED_BY_POLICY.value},
            "sheypoor": {"status": SourceStatus.DISABLED.value},
        },
    }
