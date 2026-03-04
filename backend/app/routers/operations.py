import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_db, get_current_player
from app.core.websocket_manager import manager
from app.models.player import Player, Operation
from app.schemas.operations import OperationCreate, OperationPhaseAction
from app.services import operation_service
from app.services.prison_service import get_prison_status

router = APIRouter(prefix="/operations", tags=["operations"])


async def _check_not_imprisoned(db: AsyncSession, player: Player):
    status = await get_prison_status(db, player.id)
    if status["in_prison"]:
        raise HTTPException(
            status_code=403,
            detail={
                "message": "You're inside. No operations.",
                "release_at": status["record"]["release_at"] if status["record"] else None,
            }
        )


@router.post("")
async def create_operation(
    data: OperationCreate,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    await _check_not_imprisoned(db, player)
    try:
        op = await operation_service.create_operation(db, player, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    phase_data = op.phase_data or {}
    return {
        "id": str(op.id),
        "status": op.status,
        "current_phase": op.status,
        "node_key": phase_data.get("node_key"),
        "approach": op.approach,
        "phase_data": {k: v for k, v in phase_data.items() if k != "phase_results"},
        "heat_generated": op.heat_generated,
        "artifacts_left": op.artifacts_left,
        "started_at": op.started_at.isoformat(),
        "briefing": phase_data.get("briefing", ""),
    }


@router.get("")
async def list_operations(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Operation)
        .where(Operation.player_id == player.id)
        .order_by(Operation.started_at.desc())
        .limit(20)
    )
    ops = list(result.scalars().all())
    return [
        {
            "id": str(op.id),
            "status": op.status,
            "node_key": op.phase_data.get("node_key") if op.phase_data else None,
            "approach": op.approach,
            "crypto_earned": op.crypto_earned,
            "heat_generated": op.heat_generated,
            "started_at": op.started_at.isoformat(),
            "completed_at": op.completed_at.isoformat() if op.completed_at else None,
        }
        for op in ops
    ]


@router.get("/{operation_id}")
async def get_operation(
    operation_id: uuid.UUID,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Operation).where(
            Operation.id == operation_id,
            Operation.player_id == player.id,
        )
    )
    op = result.scalar_one_or_none()
    if not op:
        raise HTTPException(status_code=404, detail="Ghost not found.")

    return {
        "id": str(op.id),
        "status": op.status,
        "current_phase": op.status,
        "phase_data": op.phase_data,
        "heat_generated": op.heat_generated,
        "artifacts_left": op.artifacts_left,
        "started_at": op.started_at.isoformat(),
    }


@router.post("/{operation_id}/phase")
async def advance_phase(
    operation_id: uuid.UUID,
    action: OperationPhaseAction,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    await _check_not_imprisoned(db, player)

    result = await db.execute(
        select(Operation).where(
            Operation.id == operation_id,
            Operation.player_id == player.id,
        )
    )
    op = result.scalar_one_or_none()
    if not op:
        raise HTTPException(status_code=404, detail="Ghost not found.")

    if op.status not in ["recon", "exploit", "persist", "monetize"]:
        raise HTTPException(status_code=400, detail=f"Operation is in state '{op.status}' — cannot advance.")

    try:
        outcome = await operation_service.advance_operation(
            db, op, player, action.phase_action, action.parameters, manager
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return outcome


@router.post("/{operation_id}/abort")
async def abort_operation(
    operation_id: uuid.UUID,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Operation).where(
            Operation.id == operation_id,
            Operation.player_id == player.id,
        )
    )
    op = result.scalar_one_or_none()
    if not op:
        raise HTTPException(status_code=404, detail="Ghost not found.")

    if op.status not in ["recon", "exploit", "persist", "monetize"]:
        raise HTTPException(status_code=400, detail="Cannot abort operation in current state.")

    return await operation_service.abort_operation(db, op, player)


@router.get("/{operation_id}/result")
async def operation_result(
    operation_id: uuid.UUID,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Operation).where(
            Operation.id == operation_id,
            Operation.player_id == player.id,
        )
    )
    op = result.scalar_one_or_none()
    if not op:
        raise HTTPException(status_code=404, detail="Ghost not found.")

    if op.status not in ["complete", "failed", "aborted"]:
        raise HTTPException(status_code=400, detail="Operation not yet complete.")

    return await operation_service.get_operation_result(db, op)
