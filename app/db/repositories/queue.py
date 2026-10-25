from datetime import datetime, timedelta, timezone
from typing import Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.job import JobQueue


async def enqueue_job(
    session: AsyncSession,
    job_type: str,
    payload: dict[str, Any],
    run_after: datetime | None = None,
) -> JobQueue:
    """Enqueues a durable job for background workers."""
    now = datetime.now(timezone.utc)
    job = JobQueue(
        job_type=job_type,
        payload=payload,
        status="pending",
        run_after=run_after or now,
        created_at=now,
    )
    session.add(job)
    await session.flush()
    return job


async def claim_next_job(
    session: AsyncSession,
    worker_id: str,
    supported_types: list[str] | None = None,
) -> JobQueue | None:
    """
    Claims the next available due job using FOR UPDATE SKIP LOCKED.
    Prevents race conditions between multiple concurrent workers.
    """
    now = datetime.now(timezone.utc)
    query = (
        select(JobQueue)
        .where(
            JobQueue.status == "pending",
            JobQueue.run_after <= now,
        )
        .order_by(JobQueue.run_after.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )

    if supported_types:
        query = query.where(JobQueue.job_type.in_(supported_types))

    result = await session.execute(query)
    job = result.scalars().first()

    if job:
        job.status = "processing"
        job.locked_at = now
        job.locked_by = worker_id
        await session.flush()

    return job


async def complete_job(session: AsyncSession, job_id: int) -> None:
    """Marks a completed job."""
    result = await session.execute(select(JobQueue).where(JobQueue.id == job_id))
    job = result.scalars().first()
    if job:
        job.status = "completed"
        await session.flush()


async def fail_job(
    session: AsyncSession,
    job_id: int,
    error_message: str,
    retry_delay_seconds: int = 60,
    max_retries: int = 3,
) -> None:
    """Records an error and reschedules or fails the job."""
    result = await session.execute(select(JobQueue).where(JobQueue.id == job_id))
    job = result.scalars().first()
    if not job:
        return

    job.error_count += 1
    job.last_error = error_message[:500]
    job.locked_by = None
    job.locked_at = None

    if job.error_count >= max_retries:
        job.status = "failed"
    else:
        job.status = "pending"
        job.run_after = datetime.now(timezone.utc) + timedelta(seconds=retry_delay_seconds)

    await session.flush()
