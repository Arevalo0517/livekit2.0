import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin_key
from api.database import get_db
from api.models import Client
from api.schemas import ClientCreate, ClientOut, ClientUpdate, MessageOut

router = APIRouter(
    prefix="/admin/clients",
    tags=["admin-clients"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("", response_model=list[ClientOut])
async def list_clients(
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[Client]:
    q = select(Client).order_by(Client.created_at.desc())
    if status:
        q = q.where(Client.status == status)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(
    body: ClientCreate,
    db: AsyncSession = Depends(get_db),
) -> Client:
    client = Client(**body.model_dump())
    db.add(client)
    await db.flush()
    await db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientOut)
async def get_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Client:
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/{client_id}", response_model=ClientOut)
async def update_client(
    client_id: uuid.UUID,
    body: ClientUpdate,
    db: AsyncSession = Depends(get_db),
) -> Client:
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    client.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", response_model=MessageOut)
async def deactivate_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalar_one_or_none()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    client.status = "cancelled"
    client.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return {"message": f"Client {client_id} deactivated"}
