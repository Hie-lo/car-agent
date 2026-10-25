from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.listing import ListingModel
from app.db.models.notification import NotificationRecord
from app.db.models.watch import Watch
from app.db.repositories.queue import enqueue_job
from app.domain.enums import BudgetMode, WatchStatus
from app.domain.listing import Listing
from app.domain.matching import MatchResult
from app.domain.vehicle_query import WatchRequest
from app.services.matching import evaluate_match


def _to_watch_request(w: Watch) -> WatchRequest:
    return WatchRequest(
        id=w.id,
        user_id=w.user_id,
        make=w.make,
        model=w.model,
        trim=w.trim,
        year_min=w.year_min,
        year_max=w.year_max,
        budget_min=w.budget_min,
        budget_max=w.budget_max,
        budget_mode=BudgetMode(w.budget_mode),
        max_overage_pct=w.max_overage_pct,
        mileage_max=w.mileage_max,
        city=w.city,
        hard_constraints=w.hard_constraints or {},
        status=WatchStatus(w.status),
    )


async def match_listing_against_watches(
    session: AsyncSession,
    listing: Listing,
    listing_db_id: int,
) -> list[tuple[Watch, MatchResult]]:
    """
    Matches an incoming normalized listing against active user watch requests:
    - Queries active, non-expired watches
    - Applies Stage A (hard filters) & Stage B (scoring)
    - If eligible and score >= 70, creates a NotificationRecord (preventing duplicates)
      and enqueues a send_notification job
    """
    now = datetime.now(timezone.utc)
    stmt = (
        select(Watch)
        .where(
            Watch.status == "active",
            (Watch.expires_at == None) | (Watch.expires_at > now),
        )
    )

    if listing.make:
        stmt = stmt.where(Watch.make == listing.make)
    if listing.model:
        stmt = stmt.where(Watch.model == listing.model)

    result = await session.execute(stmt)
    active_watches = result.scalars().all()

    matched_pairs: list[tuple[Watch, MatchResult]] = []

    for watch_db in active_watches:
        watch_req = _to_watch_request(watch_db)
        eval_res = evaluate_match(watch_req, listing)

        if eval_res.is_eligible and eval_res.match_score >= 70.0:
            # Check deduplication: have we already notified this watch for this listing?
            existing_notif = await session.execute(
                select(NotificationRecord).where(
                    NotificationRecord.watch_id == watch_db.id,
                    NotificationRecord.listing_id == listing_db_id,
                )
            )
            if existing_notif.scalars().first() is None:
                notif = NotificationRecord(
                    watch_id=watch_db.id,
                    listing_id=listing_db_id,
                    match_score=eval_res.match_score,
                    reason_codes=eval_res.reason_codes,
                    sent_at=now,
                )
                session.add(notif)

                # Enqueue background notification delivery job
                await enqueue_job(
                    session=session,
                    job_type="send_notification",
                    payload={
                        "user_id": watch_db.user_id,
                        "watch_id": watch_db.id,
                        "listing_id": listing_db_id,
                        "match_score": eval_res.match_score,
                        "reasons": eval_res.reasons,
                        "url": listing.url,
                        "price_toman": listing.price_toman,
                    },
                )
                matched_pairs.append((watch_db, eval_res))

    await session.flush()
    return matched_pairs
