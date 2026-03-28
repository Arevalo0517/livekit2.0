import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.request_validator import RequestValidator
from twilio.twiml.voice_response import Dial, VoiceResponse

from api.config import Settings, get_settings
from api.database import get_db
from api.models import Call
from api.services.call_logger import get_agent_by_phone

logger = logging.getLogger(__name__)
router = APIRouter()


def _validate_twilio_signature(
    request: Request, form_data: dict, settings: Settings
) -> bool:
    """
    Validate that the request genuinely came from Twilio.
    Reconstructs the HTTPS URL when behind an nginx reverse proxy.
    """
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    url = str(request.url)
    forwarded_proto = request.headers.get("x-forwarded-proto")
    if forwarded_proto:
        scheme = request.url.scheme
        url = url.replace(f"{scheme}://", f"{forwarded_proto}://", 1)
    twilio_signature = request.headers.get("X-Twilio-Signature", "")
    return validator.validate(url, form_data, twilio_signature)


@router.post("/voice", response_class=Response)
async def twilio_voice_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> Response:
    """
    Handle inbound Twilio voice calls.

    Flow:
    1. Validate Twilio signature (production only)
    2. Look up agent by called phone number
    3. Create pending call record in DB (room name filled in by agent worker)
    4. Return TwiML: connect caller to LiveKit SIP endpoint
       - SIP username = Twilio CallSid so the agent worker can look up the call record
    """
    form_data = await request.form()
    form_dict = dict(form_data)
    call_sid = str(form_data.get("CallSid", ""))
    from_number = str(form_data.get("From", ""))
    to_number = str(form_data.get("To", ""))

    logger.info(
        f"Inbound call: sid={call_sid}, from={from_number}, to={to_number}"
    )

    # Validate Twilio signature in production
    if settings.ENVIRONMENT == "production":
        if not _validate_twilio_signature(request, form_dict, settings):
            logger.warning(f"Invalid Twilio signature for call {call_sid}")
            response = VoiceResponse()
            response.say("Unauthorized request.", language="en-US")
            response.hangup()
            return Response(content=str(response), media_type="application/xml")

    # Look up agent by the called phone number
    agent = await get_agent_by_phone(db, to_number)
    if agent is None:
        logger.warning(f"No active agent for number: {to_number}")
        response = VoiceResponse()
        response.say(
            "This number is not configured. Goodbye.", language="en-US"
        )
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Create a pending call record.
    # The agent worker will fill in livekit_room_name and set status=in_progress
    # once it receives the job from LiveKit.
    try:
        call = Call(
            agent_id=agent.id,
            caller_number=from_number or None,
            twilio_call_sid=call_sid,
            livekit_room_name=None,
            status="pending",
            started_at=datetime.now(timezone.utc),
        )
        db.add(call)
        await db.commit()
    except Exception as exc:
        logger.error(f"Failed to create call record for {call_sid}: {exc}")
        response = VoiceResponse()
        response.say(
            "We are unable to connect your call. Please try again later.",
            language="en-US",
        )
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Build TwiML: connect Twilio to LiveKit via SIP.
    # Username = Twilio CallSid → agent worker reads sip.to attribute to find the call record.
    # The LiveKit dispatch rule (Individual type) will auto-create a room for this call.
    if not settings.LIVEKIT_SIP_HOST:
        logger.error("LIVEKIT_SIP_HOST not configured")
        response = VoiceResponse()
        response.say("Service not configured.", language="en-US")
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    sip_uri = f"sip:{call_sid}@{settings.LIVEKIT_SIP_HOST};transport=tcp"
    response = VoiceResponse()
    dial = Dial()
    dial.sip(sip_uri)
    response.append(dial)

    logger.info(f"Routing call {call_sid} to LiveKit SIP: {sip_uri}")
    return Response(content=str(response), media_type="application/xml")


@router.post("/status", response_class=Response)
async def twilio_status_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """
    Handle Twilio call status callbacks.
    Updates call records when Twilio reports a call ended.
    """
    form_data = await request.form()
    call_sid = str(form_data.get("CallSid", ""))
    call_status = str(form_data.get("CallStatus", ""))

    logger.info(f"Status callback: sid={call_sid}, status={call_status}")

    if call_status in ("failed", "busy", "no-answer", "canceled"):
        result = await db.execute(
            select(Call).where(
                Call.twilio_call_sid == call_sid,
                Call.status.in_(["pending", "in_progress"]),
            )
        )
        call = result.scalar_one_or_none()
        if call:
            db_status = (
                "abandoned"
                if call_status in ("no-answer", "canceled")
                else "failed"
            )
            call.ended_at = datetime.now(timezone.utc)
            call.status = db_status
            call.call_metadata = {
                **call.call_metadata,
                "error": f"Twilio reported: {call_status}",
            }
            await db.flush()
            logger.info(f"Marked call {call.id} as {db_status}")

    return Response(content="", status_code=204)
