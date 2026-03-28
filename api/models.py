import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Computed,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TIMESTAMP

from api.database import Base


class Client(Base):
    """Represents a client (company or individual) subscribing to the service."""

    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    billing_plan: Mapped[str] = mapped_column(
        String(50), nullable=False, default="basic"
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    agents: Mapped[list["Agent"]] = relationship("Agent", back_populates="client")
    users: Mapped[list["User"]] = relationship("User", back_populates="client")


class Agent(Base):
    """Represents a voice AI agent, each belonging to one client."""

    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    twilio_phone_number: Mapped[str | None] = mapped_column(String(50))
    livekit_agent_name: Mapped[str | None] = mapped_column(String(255), unique=True)
    system_prompt: Mapped[str] = mapped_column(
        Text, nullable=False, default="You are a helpful assistant."
    )
    voice_id: Mapped[str] = mapped_column(
        String(100), nullable=False, default="default"
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="es")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="active")
    config: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="agents")
    calls: Mapped[list["Call"]] = relationship("Call", back_populates="agent")


class Call(Base):
    """Represents a phone call handled by an agent."""

    __tablename__ = "calls"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    caller_number: Mapped[str | None] = mapped_column(String(50))
    twilio_call_sid: Mapped[str | None] = mapped_column(String(100), unique=True)
    livekit_room_name: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    # GENERATED ALWAYS AS STORED — computed column, never written by the ORM
    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        Computed(
            "CASE WHEN ended_at IS NOT NULL "
            "THEN EXTRACT(EPOCH FROM (ended_at - started_at))::INTEGER "
            "ELSE NULL END",
            persisted=True,
        ),
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="in_progress"
    )
    transcript: Mapped[str | None] = mapped_column(Text)
    recording_url: Mapped[str | None] = mapped_column(Text)
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="calls")


class CallMetric(Base):
    """Represents daily aggregated metrics per agent for fast dashboard queries."""

    __tablename__ = "call_metrics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    total_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    abandoned_calls: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_duration_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    avg_duration_seconds: Mapped[float | None] = mapped_column(Numeric(10, 2))

    __table_args__ = (UniqueConstraint("agent_id", "date"),)


class User(Base):
    """Represents a user with dashboard login credentials."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="viewer")
    last_login: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    client: Mapped["Client"] = relationship("Client", back_populates="users")


class AuditLog(Base):
    """Tracks all admin actions for debugging and compliance."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50))
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    performed_by: Mapped[str] = mapped_column(
        String(255), nullable=False, default="admin"
    )
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=func.now()
    )
