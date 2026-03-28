"""
Synchronous database client for the LiveKit agent worker.
The agent runs as a standalone process — sync SQLAlchemy is simpler here.
"""
import json
import logging
import os

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

_DATABASE_URL = os.environ["DATABASE_URL"]
_engine = create_engine(_DATABASE_URL, pool_size=3, max_overflow=2)
_Session = sessionmaker(bind=_engine)


def get_agent_config_by_call_sid(twilio_call_sid: str, room_name: str) -> dict | None:
    """
    Look up agent config using the Twilio CallSid embedded in the SIP URI username.

    The webhook stores a 'pending' call record keyed by twilio_call_sid.
    This function:
    1. Finds that pending call
    2. Updates it with the LiveKit room name and sets status=in_progress
    3. Returns the agent configuration needed to run the voice pipeline

    Args:
        twilio_call_sid: Twilio Call-ID (e.g. CA1a2b3c...)
        room_name: LiveKit room name auto-created by the SIP dispatch rule
    """
    with _Session() as session:
        # Step 1: find the pending call record
        call_row = session.execute(
            text("""
                SELECT c.id AS call_id, c.agent_id
                FROM calls c
                WHERE c.twilio_call_sid = :call_sid
                  AND c.status = 'pending'
                LIMIT 1
            """),
            {"call_sid": twilio_call_sid},
        ).fetchone()

        if call_row is None:
            logger.warning(
                f"No pending call found for twilio_call_sid={twilio_call_sid}"
            )
            return None

        # Step 2: update room name and mark in_progress
        session.execute(
            text("""
                UPDATE calls
                SET livekit_room_name = :room_name,
                    status = 'in_progress'
                WHERE id = CAST(:call_id AS uuid)
            """),
            {"call_id": str(call_row.call_id), "room_name": room_name},
        )

        # Step 3: load agent config
        agent_row = session.execute(
            text("""
                SELECT system_prompt, voice_id, language, config
                FROM agents
                WHERE id = CAST(:agent_id AS uuid)
            """),
            {"agent_id": str(call_row.agent_id)},
        ).fetchone()

        session.commit()

    if agent_row is None:
        logger.error(f"Agent not found for id={call_row.agent_id}")
        return None

    return {
        "call_id": str(call_row.call_id),
        "agent_id": str(call_row.agent_id),
        "system_prompt": agent_row.system_prompt,
        "voice_id": agent_row.voice_id,
        "language": agent_row.language,
        "config": agent_row.config or {},
    }


def save_partial_transcript(call_id: str, partial: str) -> None:
    """Persist partial transcript to metadata for crash recovery."""
    partial_json = json.dumps(partial)
    with _Session() as session:
        session.execute(
            text("""
                UPDATE calls
                SET metadata = jsonb_set(
                    COALESCE(metadata, '{}'),
                    '{partial_transcript}',
                    :partial_json
                )
                WHERE id = CAST(:call_id AS uuid)
            """),
            {"call_id": call_id, "partial_json": partial_json},
        )
        session.commit()


def complete_call(call_id: str, transcript: str, status: str = "completed") -> None:
    """Mark a call complete with its full transcript."""
    with _Session() as session:
        session.execute(
            text("""
                UPDATE calls
                SET ended_at   = NOW(),
                    transcript = :transcript,
                    status     = :status
                WHERE id = CAST(:call_id AS uuid)
            """),
            {"call_id": call_id, "transcript": transcript, "status": status},
        )
        session.commit()
    logger.info(f"Call {call_id} marked {status}")


def fail_call(call_id: str, error: str) -> None:
    """Mark a call as failed with error details in metadata."""
    error_json = json.dumps(error)
    with _Session() as session:
        session.execute(
            text("""
                UPDATE calls
                SET ended_at = NOW(),
                    status   = 'failed',
                    metadata = jsonb_set(
                        COALESCE(metadata, '{}'),
                        '{error}',
                        :error_json
                    )
                WHERE id = CAST(:call_id AS uuid)
            """),
            {"call_id": call_id, "error_json": error_json},
        )
        session.commit()
    logger.info(f"Call {call_id} marked failed: {error}")
