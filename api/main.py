import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI
from sqlalchemy import text

from api.config import get_settings
from api.database import async_session_maker
from api.routers.agents import router as agents_router
from api.routers.calls import router as calls_router
from api.routers.clients import router as clients_router
from api.routers.webhook import router as webhook_router
from api.services.call_logger import aggregate_daily_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def _daily_metrics_loop() -> None:
    """Background task: aggregate yesterday's call metrics every hour."""
    while True:
        try:
            yesterday = date.today() - timedelta(days=1)
            async with async_session_maker() as db:
                await aggregate_daily_metrics(db, yesterday)
                await db.commit()
            logger.info(f"Daily metrics aggregated for {yesterday}")
        except Exception as exc:
            logger.error(f"Failed to aggregate daily metrics: {exc}")
        await asyncio.sleep(3600)  # Run every hour


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate settings on startup — raises immediately if env vars are missing
    settings = get_settings()
    logger.info(
        f"Starting VoiceAI API | env={settings.ENVIRONMENT} | domain={settings.DOMAIN}"
    )

    # Start background metrics aggregation task
    metrics_task = asyncio.create_task(_daily_metrics_loop())

    yield

    # Graceful shutdown
    metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        pass
    logger.info("VoiceAI API shut down cleanly")


app = FastAPI(title="VoiceAI API", version="0.1.0", lifespan=lifespan)

# Routers
app.include_router(webhook_router, prefix="/webhook/twilio", tags=["webhook"])

# Admin API — protected by X-Admin-Key header
app.include_router(clients_router)
app.include_router(agents_router)
app.include_router(calls_router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Basic liveness probe."""
    return {"status": "ok", "service": "api"}


@app.get("/health/db", tags=["health"])
async def health_db() -> dict:
    """Database connectivity probe."""
    try:
        async with async_session_maker() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        return {"status": "error", "database": str(exc)}
