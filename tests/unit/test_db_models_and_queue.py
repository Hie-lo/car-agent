import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.db.models import CreditLedger, JobQueue, ListingModel, NotificationRecord, User, Watch
from app.db.repositories.queue import claim_next_job, complete_job, enqueue_job, fail_job
from app.db.session import Base


@pytest.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


class TestDatabaseModelsAndQueue:
    @pytest.mark.asyncio
    async def test_user_and_watch_creation(self, async_db):
        user = User(telegram_id=987654321, plan_tier="pro", daily_credits_remaining=10)
        async_db.add(user)
        await async_db.flush()
        assert user.id is not None

        watch = Watch(
            id="watch_abc",
            user_id=user.id,
            make="پژو",
            model="207",
            budget_max=1_500_000_000,
            status="active",
        )
        async_db.add(watch)
        await async_db.flush()
        assert watch.id == "watch_abc"

    @pytest.mark.asyncio
    async def test_duplicate_listing_constraint(self, async_db):
        l1 = ListingModel(
            source_id="divar",
            source_listing_id="post_uniq_1",
            title="تیبا",
            url="https://divar.ir/v/1",
        )
        async_db.add(l1)
        await async_db.flush()

        # Same source_id and source_listing_id must trigger IntegrityError
        l2 = ListingModel(
            source_id="divar",
            source_listing_id="post_uniq_1",
            title="تیبا تکراری",
            url="https://divar.ir/v/1",
        )
        async_db.add(l2)
        with pytest.raises(IntegrityError):
            await async_db.flush()

    @pytest.mark.asyncio
    async def test_credit_ledger_idempotency_constraint(self, async_db):
        user = User(telegram_id=111, plan_tier="free")
        async_db.add(user)
        await async_db.flush()

        c1 = CreditLedger(user_id=user.id, amount=-1, transaction_type="spend", idempotency_key="key_123")
        async_db.add(c1)
        await async_db.flush()

        # Duplicate idempotency_key must trigger IntegrityError
        c2 = CreditLedger(user_id=user.id, amount=-1, transaction_type="spend", idempotency_key="key_123")
        async_db.add(c2)
        with pytest.raises(IntegrityError):
            await async_db.flush()

    @pytest.mark.asyncio
    async def test_job_queue_lifecycle(self, async_db):
        # 1. Enqueue job
        job = await enqueue_job(async_db, job_type="poll_source", payload={"source": "divar"})
        assert job.id is not None
        assert job.status == "pending"

        # 2. Claim job
        claimed = await claim_next_job(async_db, worker_id="worker_1", supported_types=["poll_source"])
        assert claimed is not None
        assert claimed.id == job.id
        assert claimed.status == "processing"
        assert claimed.locked_by == "worker_1"

        # 3. Fail and retry
        await fail_job(async_db, claimed.id, error_message="Network timeout", max_retries=2)
        assert claimed.status == "pending"
        assert claimed.error_count == 1

        # 4. Exceed retries marks failed
        await fail_job(async_db, claimed.id, error_message="Fatal error", max_retries=2)
        assert claimed.status == "failed"
        assert claimed.error_count == 2
