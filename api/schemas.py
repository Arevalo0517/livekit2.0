import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr


# ──────────────────────────────────────────────
# Clients
# ──────────────────────────────────────────────

class ClientCreate(BaseModel):
    name: str
    company_name: str | None = None
    email: EmailStr
    billing_plan: str = "basic"
    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = None
    company_name: str | None = None
    email: EmailStr | None = None
    billing_plan: str | None = None
    status: str | None = None
    notes: str | None = None


class ClientOut(BaseModel):
    id: uuid.UUID
    name: str
    company_name: str | None
    email: str
    status: str
    billing_plan: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Agents
# ──────────────────────────────────────────────

class AgentCreate(BaseModel):
    client_id: uuid.UUID
    name: str
    twilio_phone_number: str | None = None
    system_prompt: str = "You are a helpful assistant."
    voice_id: str = "luna"
    language: str = "es"
    config: dict[str, Any] = {}


class AgentUpdate(BaseModel):
    name: str | None = None
    twilio_phone_number: str | None = None
    system_prompt: str | None = None
    voice_id: str | None = None
    language: str | None = None
    status: str | None = None
    config: dict[str, Any] | None = None


class AgentOut(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    name: str
    twilio_phone_number: str | None
    system_prompt: str
    voice_id: str
    language: str
    status: str
    config: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Calls
# ──────────────────────────────────────────────

class CallOut(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    caller_number: str | None
    twilio_call_sid: str | None
    livekit_room_name: str | None
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None
    status: str
    transcript: str | None
    recording_url: str | None

    model_config = {"from_attributes": True}


class CallListOut(BaseModel):
    items: list[CallOut]
    total: int
    page: int
    limit: int


# ──────────────────────────────────────────────
# Generic
# ──────────────────────────────────────────────

class MessageOut(BaseModel):
    message: str
