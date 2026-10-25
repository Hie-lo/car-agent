from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.listing import ListingModel
from app.domain.enums import PriceMode
from app.domain.listing import Listing
from app.services.deduplication import should_renotify
from app.sources.base import BaseListingSource
from app.workers.matcher import match_listing_against_watches


def _to_domain_listing(model: ListingModel) -> Listing:
    return Listing(
        source_id=model.source_id,
        source_listing_id=model.source_listing_id,
        title=model.title,
        url=model.url,
        make=model.make,
        model=model.model,
        trim=model.trim,
        model_year=model.model_year,
        mileage=model.mileage,
        price_toman=model.price_toman,
        price_mode=PriceMode(model.price_mode),
        city=model.city,
        color=model.color,
        body_condition=model.body_condition,
        engine_condition=model.engine_condition,
        gearbox=model.gearbox,
        is_active=model.is_active,
        first_observed=model.first_observed,
        last_observed=model.last_observed,
    )


async def process_incoming_listings(
    session: AsyncSession,
    source: BaseListingSource,
    raw_posts: list[dict],
) -> int:
    """
    Normalizes and ingests source listings:
    1. Ensures source is approved (fails closed otherwise)
    2. Upserts canonical ListingModel records
    3. Triggers matching only for new listings or material changes (e.g. meaningful price reduction)
    Returns number of newly ingested or re-notified listings.
    """
    source.check_runnable()
    now = datetime.now(timezone.utc)
    processed_count = 0

    for raw in raw_posts:
        listing = source.parse_post(raw)

        # Check existing listing in DB
        result = await session.execute(
            select(ListingModel).where(
                ListingModel.source_id == listing.source_id,
                ListingModel.source_listing_id == listing.source_listing_id,
            )
        )
        existing = result.scalars().first()

        if existing is None:
            # 1. New listing
            db_listing = ListingModel(
                source_id=listing.source_id,
                source_listing_id=listing.source_listing_id,
                title=listing.title,
                url=listing.url,
                make=listing.make,
                model=listing.model,
                trim=listing.trim,
                model_year=listing.model_year,
                mileage=listing.mileage,
                price_toman=listing.price_toman,
                price_mode=listing.price_mode.value,
                city=listing.city,
                color=listing.color,
                body_condition=listing.body_condition,
                engine_condition=listing.engine_condition,
                gearbox=listing.gearbox,
                is_active=listing.is_active,
                first_observed=now,
                last_observed=now,
            )
            session.add(db_listing)
            await session.flush()

            # Match against active watches
            await match_listing_against_watches(session, listing, db_listing.id)
            processed_count += 1
        else:
            # 2. Existing listing: check for material changes
            prev_domain = _to_domain_listing(existing)
            if should_renotify(prev_domain, listing):
                existing.price_toman = listing.price_toman
                existing.is_active = listing.is_active
                existing.last_observed = now
                await session.flush()

                # Re-match with updated price
                await match_listing_against_watches(session, listing, existing.id)
                processed_count += 1
            else:
                existing.last_observed = now

    await session.flush()
    return processed_count
