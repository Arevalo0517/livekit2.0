import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin_key
from api.database import get_db
from api.models import Agent, Client
from api.schemas import AgentCreate, AgentOut, AgentUpdate, MessageOut

router = APIRouter(
    prefix="/admin/agents",
    tags=["admin-agents"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("", response_model=list[AgentOut])
async def list_agents(
    client_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[Agent]:
    q = select(Agent).order_by(Agent.created_at.desc())
    if client_id:
        q = q.where(Agent.client_id == client_id)
    if status:
        q = q.where(Agent.status == status)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("", response_model=AgentOut, status_code=status.HTTP_201_CREATED)
async def create_agent(
    body: AgentCreate,
    db: AsyncSession = Depends(get_db),
) -> Agent:
    # Verify client exists
    client_result = await db.execute(
        select(Client).where(Client.id == body.client_id)
    )
    if client_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Client not found")

    agent = Agent(**body.model_dump())
    db.add(agent)
    await db.flush()
    await db.refresh(agent)
    return agent


@router.get("/{agent_id}", response_model=AgentOut)
async def get_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Agent:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.patch("/{agent_id}", response_model=AgentOut)
async def update_agent(
    agent_id: uuid.UUID,
    body: AgentUpdate,
    db: AsyncSession = Depends(get_db),
) -> Agent:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(agent, field, value)
    agent.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}", response_model=MessageOut)
async def deactivate_agent(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = "inactive"
    agent.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return {"message": f"Agent {agent_id} deactivated"}
