import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin_key
from api.database import get_db
from api.models import Call
from api.schemas import CallListOut, CallOut

router = APIRouter(
    prefix="/admin/calls",
    tags=["admin-calls"],
    dependencies=[Depends(require_admin_key)],
)


@router.get("", response_model=CallListOut)
async def list_calls(
    agent_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> CallListOut:
    q = select(Call).order_by(Call.started_at.desc())
    if agent_id:
        q = q.where(Call.agent_id == agent_id)
    if status:
        q = q.where(Call.status == status)

    # Total count
    count_result = await db.execute(
        select(func.count()).select_from(q.subquery())
    )
    total = count_result.scalar_one()

    # Paginated rows
    rows_result = await db.execute(q.offset((page - 1) * limit).limit(limit))
    items = list(rows_result.scalars().all())

    return CallListOut(items=items, total=total, page=page, limit=limit)


@router.get("/{call_id}", response_model=CallOut)
async def get_call(
    call_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Call:
    result = await db.execute(select(Call).where(Call.id == call_id))
    call = result.scalar_one_or_none()
    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")
    return call
