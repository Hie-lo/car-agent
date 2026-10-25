import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from app.db.models import JobQueue, User, Watch
from app.db.session import Base
from app.services.admin import get_system_metrics


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


class TestAdminMetrics:
    @pytest.mark.asyncio
    async def test_get_system_metrics_aggregations(self, async_db):
        # Setup sample data
        user = User(telegram_id=123, plan_tier="free")
        async_db.add(user)
        await async_db.flush()

        watch = Watch(id="w1", user_id=user.id, make="تارا", model="", status="active")
        async_db.add(watch)

        job = JobQueue(job_type="test", payload={}, status="pending")
        async_db.add(job)
        await async_db.flush()

        metrics = await get_system_metrics(async_db)
        assert metrics["users"]["total"] == 1
        assert metrics["watches"]["active"] == 1
        assert metrics["queue"]["pending"] == 1
        assert metrics["queue"]["is_healthy"] is True
        assert metrics["sources"]["divar"]["status"] == "approved"
        assert metrics["sources"]["bama"]["status"] == "blocked_by_policy"
