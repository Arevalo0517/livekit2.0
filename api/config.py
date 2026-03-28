from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # API Security
    SECRET_KEY: str
    ADMIN_API_KEY: str

    # LiveKit
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str

    # LiveKit SIP — trunk ID and project SIP hostname (from LiveKit Cloud → Telephony → Dispatch Rules)
    LIVEKIT_SIP_TRUNK_ID: str = ""
    LIVEKIT_SIP_HOST: str = ""  # e.g. 4dp826keg0d.sip.livekit.cloud

    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str

    # Deepgram
    DEEPGRAM_API_KEY: str

    # Rime
    RIME_API_KEY: str

    # OpenAI
    OPENAI_API_KEY: str

    # App
    ENVIRONMENT: str = "production"
    DOMAIN: str = ""

    model_config = {"env_file": ".env", "case_sensitive": True}


@lru_cache
def get_settings() -> Settings:
    return Settings()
