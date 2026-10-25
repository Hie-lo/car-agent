import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.db.models import JobQueue, ListingModel, NotificationRecord, User, Watch
from app.db.session import Base
from app.domain.enums import PriceMode, SourceStatus
from app.domain.listing import Listing
from app.sources.divar import DivarKenarSource
from app.sources.registry import SourceRegistryEntry
from app.workers.collector import process_incoming_listings
from app.workers.matcher import match_listing_against_watches


@pytest.fixture
async def async_db():
    pytest.importorskip("aiosqlite", reason="aiosqlite required for in-memory SQLite tests")
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


class TestWorkersPipeline:
    @pytest.mark.asyncio
    async def test_matcher_enqueues_notification_and_deduplicates(self, async_db):
        # 1. Setup user and watch
        user = User(telegram_id=12345, plan_tier="pro")
        async_db.add(user)
        await async_db.flush()

        watch = Watch(
            id="watch_207",
            user_id=user.id,
            make="پژو",
            model="207",
            budget_max=700_000_000,
            status="active",
        )
        async_db.add(watch)

        # 2. Setup listing
        listing_model = ListingModel(
            source_id="divar",
            source_listing_id="post_207_1",
            title="پژو 207 سفید",
            url="https://divar.ir/v/post_207_1",
            make="پژو",
            model="207",
            price_toman=680_000_000,
        )
        async_db.add(listing_model)
        await async_db.flush()

        domain_listing = Listing(
            source_id="divar",
            source_listing_id="post_207_1",
            title="پژو 207 سفید",
            url="https://divar.ir/v/post_207_1",
            make="پژو",
            model="207",
            price_toman=680_000_000,
            price_mode=PriceMode.FIXED,
        )

        # 3. First match: must match and enqueue notification
        matched = await match_listing_against_watches(async_db, domain_listing, listing_model.id)
        assert len(matched) == 1
        assert matched[0][0].id == "watch_207"

        # Verify job was enqueued
        job_res = await async_db.execute(select(JobQueue).where(JobQueue.job_type == "send_notification"))
        jobs = job_res.scalars().all()
        assert len(jobs) == 1
        assert jobs[0].payload["watch_id"] == "watch_207"

        # 4. Second match: must NOT duplicate notification
        matched_second = await match_listing_against_watches(async_db, domain_listing, listing_model.id)
        assert len(matched_second) == 0

    @pytest.mark.asyncio
    async def test_collector_material_price_drop_triggers_rematch(self, async_db):
        user = User(telegram_id=54321, plan_tier="free")
        async_db.add(user)
        await async_db.flush()

        watch = Watch(
            id="watch_tara",
            user_id=user.id,
            make="تارا",
            model="",
            budget_max=900_000_000,
            status="active",
        )
        async_db.add(watch)
        await async_db.flush()

        entry = SourceRegistryEntry(source_key="divar", display_name="Divar", status=SourceStatus.APPROVED)
        source = DivarKenarSource(entry)

        raw_post = {
            "token": "tara_100",
            "title": "تارا صفر",
            "price": {"value": 900_000_000, "type": "fixed"},
            "fields": {"brand_model": "تارا", "year": 1402},
            "city": "tehran",
        }

        # 1. Ingest initial listing (processed_count = 1)
        count1 = await process_incoming_listings(async_db, source, [raw_post])
        assert count1 == 1

        # 2. Ingest same price (no re-notification, processed_count = 0)
        count2 = await process_incoming_listings(async_db, source, [raw_post])
        assert count2 == 0

        # 3. Ingest with 5% price drop (900M -> 850M) (triggers re-match, processed_count = 1)
        dropped_post = dict(raw_post)
        dropped_post["price"] = {"value": 850_000_000, "type": "fixed"}
        count3 = await process_incoming_listings(async_db, source, [dropped_post])
        assert count3 == 1
