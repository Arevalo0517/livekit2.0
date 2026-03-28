"""
LiveKit Agent Worker — entrypoint for the Voice AI agent process.

Uses LiveKit Agents v1.3.x API:
  - AgentServer with @server.rtc_session for job dispatch
  - AgentSession for STT + LLM + TTS pipeline
  - One worker process handles up to 4 concurrent calls (t3.medium capacity)
"""
import logging
import os

from livekit.agents import AutoSubscribe, JobContext, cli
from livekit.agents.voice import AgentSession  # noqa: F401 (re-exported for clarity)
from livekit.agents import AgentServer

from agent.db import (
    complete_call,
    fail_call,
    get_agent_config_by_room,
    save_partial_transcript,
)
from agent.pipeline import build_agent, build_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = AgentServer()


@server.rtc_session()
async def voice_agent_session(ctx: JobContext) -> None:
    """
    Entry point for each inbound call job.
    Called by LiveKit when a new room is created.
    """
    room_name = ctx.room.name
    call_id: str | None = None
    transcript_parts: list[str] = []

    logger.info(f"Agent job started: room={room_name}")

    # Connect to the room (audio only — no video)
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Load agent configuration from DB using the room name
    agent_config = get_agent_config_by_room(room_name)
    if agent_config is None:
        logger.error(f"No agent config found for room: {room_name}")
        return

    call_id = agent_config["call_id"]
    logger.info(
        f"Loaded config: call_id={call_id}, "
        f"voice={agent_config['voice_id']}, lang={agent_config['language']}"
    )

    # Build the voice pipeline and agent
    session = build_session(agent_config)
    agent = build_agent(agent_config)

    # Track transcript turns as they are committed
    @session.on("user_input_transcribed")
    def on_user_input(event) -> None:
        if event.is_final:
            transcript_parts.append(f"User: {event.transcript}")
            save_partial_transcript(call_id, "\n".join(transcript_parts))

    @session.on("conversation_item_added")
    def on_conversation_item(event) -> None:
        item = event.item
        if item.role == "assistant" and item.text_content:
            transcript_parts.append(f"Agent: {item.text_content}")
            save_partial_transcript(call_id, "\n".join(transcript_parts))

    # Start the session in the room
    try:
        await session.start(agent=agent, room=ctx.room)
        logger.info(f"Session started in room {room_name}")

        # Wait until all participants disconnect
        await ctx.wait_for_disconnect()

    except Exception as exc:
        logger.error(f"Session error in room {room_name}: {exc}")
        if call_id:
            fail_call(call_id, str(exc))
        return

    # Save final transcript and mark the call complete
    final_transcript = "\n".join(transcript_parts)
    if call_id:
        complete_call(call_id, final_transcript, "completed")
        logger.info(
            f"Call {call_id} completed — transcript: {len(final_transcript)} chars"
        )


if __name__ == "__main__":
    cli.run_app(server)
