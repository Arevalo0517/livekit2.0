import uuid
from datetime import date, datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from api.models import Agent, Call, CallMetric


async def get_agent_by_phone(db: AsyncSession, phone_number: str) -> Agent | None:
    """Look up an active agent by its Twilio phone number."""
    result = await db.execute(
        select(Agent).where(
            Agent.twilio_phone_number == phone_number,
            Agent.status == "active",
        )
    )
    return result.scalar_one_or_none()


async def create_call(
    db: AsyncSession,
    agent_id: uuid.UUID,
    caller_number: str | None,
    twilio_call_sid: str,
    livekit_room_name: str,
) -> Call:
    """Insert a new call record with status in_progress."""
    call = Call(
        agent_id=agent_id,
        caller_number=caller_number,
        twilio_call_sid=twilio_call_sid,
        livekit_room_name=livekit_room_name,
        status="in_progress",
        started_at=datetime.now(timezone.utc),
    )
    db.add(call)
    await db.flush()
    await db.refresh(call)
    return call


async def complete_call(
    db: AsyncSession,
    call_id: uuid.UUID,
    transcript: str | None = None,
    status: str = "completed",
) -> Call | None:
    """Mark a call complete with optional transcript."""
    result = await db.execute(select(Call).where(Call.id == call_id))
    call = result.scalar_one_or_none()
    if call is None:
        return None
    call.ended_at = datetime.now(timezone.utc)
    call.transcript = transcript
    call.status = status
    await db.flush()
    await db.refresh(call)
    return call


async def fail_call(
    db: AsyncSession,
    call_id: uuid.UUID,
    error_details: str,
) -> Call | None:
    """Mark a call as failed with error info stored in metadata."""
    result = await db.execute(select(Call).where(Call.id == call_id))
    call = result.scalar_one_or_none()
    if call is None:
        return None
    call.ended_at = datetime.now(timezone.utc)
    call.status = "failed"
    call.call_metadata = {**call.call_metadata, "error": error_details}
    await db.flush()
    await db.refresh(call)
    return call


async def aggregate_daily_metrics(db: AsyncSession, target_date: date) -> None:
    """
    Aggregate call metrics for target_date into the call_metrics table.
    Uses INSERT ... ON CONFLICT DO UPDATE (upsert) to be idempotent.
    """
    await db.execute(
        text("""
            INSERT INTO call_metrics (
                id, agent_id, date,
                total_calls, completed_calls, failed_calls, abandoned_calls,
                total_duration_seconds, avg_duration_seconds
            )
            SELECT
                gen_random_uuid(),
                agent_id,
                CAST(:target_date AS date),
                COUNT(*),
                COUNT(*) FILTER (WHERE status = 'completed'),
                COUNT(*) FILTER (WHERE status = 'failed'),
                COUNT(*) FILTER (WHERE status = 'abandoned'),
                COALESCE(SUM(duration_seconds), 0),
                AVG(duration_seconds)
            FROM calls
            WHERE DATE(started_at) = CAST(:target_date AS date)
            GROUP BY agent_id
            ON CONFLICT (agent_id, date)
            DO UPDATE SET
                total_calls           = EXCLUDED.total_calls,
                completed_calls       = EXCLUDED.completed_calls,
                failed_calls          = EXCLUDED.failed_calls,
                abandoned_calls       = EXCLUDED.abandoned_calls,
                total_duration_seconds = EXCLUDED.total_duration_seconds,
                avg_duration_seconds  = EXCLUDED.avg_duration_seconds
        """),
        {"target_date": target_date},
    )
