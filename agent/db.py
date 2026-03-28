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


def get_agent_config_by_room(room_name: str) -> dict | None:
    """
    Look up agent config for a given LiveKit room name.

    The room name follows the pattern 'call_{twilio_call_sid}'.
    Returns the agent's system_prompt, voice_id, language, config, and call_id.
    Returns None if no matching in-progress call is found.
    """
    with _Session() as session:
        row = session.execute(
            text("""
                SELECT
                    a.id          AS agent_id,
                    a.system_prompt,
                    a.voice_id,
                    a.language,
                    a.config,
                    c.id          AS call_id
                FROM calls c
                JOIN agents a ON a.id = c.agent_id
                WHERE c.livekit_room_name = :room_name
                  AND c.status = 'in_progress'
                LIMIT 1
            """),
            {"room_name": room_name},
        ).fetchone()

    if row is None:
        logger.warning(f"No in-progress call found for room: {room_name}")
        return None

    return {
        "agent_id": str(row.agent_id),
        "call_id": str(row.call_id),
        "system_prompt": row.system_prompt,
        "voice_id": row.voice_id,
        "language": row.language,
        "config": row.config or {},
    }


def save_partial_transcript(call_id: str, partial: str) -> None:
    """Persist partial transcript to metadata for crash recovery."""
    # Encode to JSON string in Python to avoid SQLAlchemy/psycopg2 cast issues
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
    # Encode error as JSON string in Python to avoid SQLAlchemy cast conflicts
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
