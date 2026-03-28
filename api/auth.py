from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from api.config import get_settings

_api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


async def require_admin_key(
    api_key: str | None = Security(_api_key_header),
) -> None:
    """FastAPI dependency: reject requests that don't carry the correct admin key."""
    settings = get_settings()
    if not api_key or api_key != settings.ADMIN_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Admin-Key header",
        )
