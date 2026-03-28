import logging

from livekit.api import LiveKitAPI
from livekit.api.room_service import CreateRoomRequest

from api.config import get_settings

logger = logging.getLogger(__name__)


async def create_room(room_name: str) -> dict:
    """
    Create a LiveKit room for an inbound call.

    Args:
        room_name: Unique room name, typically 'call_{twilio_call_sid}'

    Returns:
        dict with 'name' and 'sid' of the created room
    """
    settings = get_settings()
    async with LiveKitAPI(
        url=settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    ) as lk:
        room = await lk.room.create_room(
            CreateRoomRequest(
                name=room_name,
                max_participants=2,
                empty_timeout=60,  # Destroy room if empty for 60 seconds
            )
        )
    logger.info(f"Created LiveKit room: name={room.name}, sid={room.sid}")
    return {"name": room.name, "sid": room.sid}
