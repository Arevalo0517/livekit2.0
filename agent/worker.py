"""
LiveKit Agent Worker — entrypoint for the Voice AI agent process.

Uses LiveKit Agents v1.3.x API:
  - AgentServer with @server.rtc_session for job dispatch
  - AgentSession for STT + LLM + TTS pipeline
  - One worker process handles up to 4 concurrent calls (t3.medium capacity)

SIP flow:
  Twilio → SIP INVITE to LiveKit (username = Twilio CallSid)
  LiveKit dispatch rule (Individual) → auto-creates room, dispatches this worker
  Worker reads sip.to attribute from SIP participant → extracts CallSid
  Worker looks up pending call record → updates with room name → runs session
"""
import asyncio
import logging

from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, cli
from livekit.agents import AgentServer

from agent.db import (
    complete_call,
    fail_call,
    get_agent_config_by_call_sid,
    save_partial_transcript,
)
from agent.pipeline import build_agent, build_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

server = AgentServer()

_SIP_PARTICIPANT_TIMEOUT = 30.0  # seconds to wait for SIP participant to join


async def _wait_for_sip_participant(ctx: JobContext) -> rtc.RemoteParticipant | None:
    """Wait up to _SIP_PARTICIPANT_TIMEOUT seconds for a SIP participant to join."""
    # Check participants already in the room
    for participant in ctx.room.remote_participants.values():
        if participant.kind == rtc.ParticipantKind.SIP:
            return participant

    # Wait for one to join
    fut: asyncio.Future = asyncio.get_event_loop().create_future()

    def on_participant_connected(participant: rtc.RemoteParticipant) -> None:
        if participant.kind == rtc.ParticipantKind.SIP and not fut.done():
            fut.set_result(participant)

    ctx.room.on("participant_connected", on_participant_connected)
    try:
        return await asyncio.wait_for(fut, timeout=_SIP_PARTICIPANT_TIMEOUT)
    except asyncio.TimeoutError:
        return None


@server.rtc_session()
async def voice_agent_session(ctx: JobContext) -> None:
    """
    Entry point for each inbound call job.
    Called by LiveKit when a new room is created via SIP dispatch rule.
    """
    room_name = ctx.room.name
    call_id: str | None = None
    transcript_parts: list[str] = []

    logger.info(f"Agent job started: room={room_name}")

    # Connect to the room (audio only — no video)
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the SIP participant (the Twilio caller) to join
    sip_participant = await _wait_for_sip_participant(ctx)
    if sip_participant is None:
        logger.error(f"No SIP participant joined room {room_name} within timeout")
        return

    logger.info(
        f"SIP participant joined: identity={sip_participant.identity} "
        f"attributes={sip_participant.attributes}"
    )

    # Extract Twilio CallSid from the SIP 'to' attribute.
    # The webhook set the SIP username = Twilio CallSid, so LiveKit stores it in sip.to
    # as "{call_sid}@{sip_host}".
    sip_to = sip_participant.attributes.get("sip.to", "")
    twilio_call_sid = sip_to.split("@")[0].strip() if sip_to else ""

    # Fallback: try the participant identity (some LiveKit versions use it differently)
    if not twilio_call_sid:
        twilio_call_sid = sip_participant.identity.split("@")[0].strip()

    logger.info(f"Extracted twilio_call_sid={twilio_call_sid!r} from sip.to={sip_to!r}")

    if not twilio_call_sid:
        logger.error(f"Could not extract Twilio CallSid from SIP participant in room {room_name}")
        return

    # Look up pending call record by Twilio CallSid and update with room name
    agent_config = get_agent_config_by_call_sid(twilio_call_sid, room_name)
    if agent_config is None:
        logger.error(
            f"No pending call found for twilio_call_sid={twilio_call_sid}, room={room_name}"
        )
        return

    call_id = agent_config["call_id"]
    logger.info(
        f"Loaded config: call_id={call_id}, "
        f"voice={agent_config['voice_id']}, lang={agent_config['language']}"
    )

    # Build the voice pipeline and agent
    session = build_session(agent_config)
    agent = build_agent(agent_config)

    # Track transcript turns as they are committed.
    # .on() requires synchronous callbacks — async work dispatched via create_task.
    def on_user_input(event) -> None:
        if event.is_final:
            transcript_parts.append(f"User: {event.transcript}")
            snapshot = "\n".join(transcript_parts)
            asyncio.create_task(
                asyncio.get_event_loop().run_in_executor(
                    None, save_partial_transcript, call_id, snapshot
                )
            )

    def on_conversation_item(event) -> None:
        item = event.item
        if item.role == "assistant" and item.text_content:
            transcript_parts.append(f"Agent: {item.text_content}")
            snapshot = "\n".join(transcript_parts)
            asyncio.create_task(
                asyncio.get_event_loop().run_in_executor(
                    None, save_partial_transcript, call_id, snapshot
                )
            )

    session.on("user_input_transcribed", on_user_input)
    session.on("conversation_item_added", on_conversation_item)

    # Future that resolves when all remote participants have left
    disconnect_future: asyncio.Future = asyncio.get_event_loop().create_future()

    def on_participant_disconnected(participant: rtc.RemoteParticipant) -> None:
        if len(ctx.room.remote_participants) == 0:
            if not disconnect_future.done():
                disconnect_future.set_result(None)

    ctx.room.on("participant_disconnected", on_participant_disconnected)

    # Start the session
    try:
        await session.start(agent=agent, room=ctx.room)
        logger.info(f"Session started in room {room_name}")

        # Trigger greeting — agent speaks first so caller doesn't hear silence
        await session.generate_reply()

        # Wait until all participants disconnect
        await disconnect_future

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
