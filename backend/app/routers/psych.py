from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_player
from app.models.player import Player
from app.services.psych_service import (
    apply_psych_consequences, get_state_description,
    go_dark_recovery, use_stimulant, use_sedative, get_psych_forecast,
)
from app.services.player_service import get_player_psych

router = APIRouter(prefix="/psych", tags=["psych"])


@router.get("/state")
async def psych_state(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    psych = await get_player_psych(db, player.id)
    if not psych:
        raise HTTPException(status_code=404, detail="Psych state not found.")
    return get_state_description(psych)


@router.get("/modifiers")
async def psych_modifiers(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    return await apply_psych_consequences(db, player.id)


@router.post("/recover/dark")
async def recover_dark(
    hours: int = Query(default=8, ge=1, le=72),
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    await go_dark_recovery(db, player.id, hours)
    psych = await get_player_psych(db, player.id)
    return {
        "recovered": True,
        "hours": hours,
        "state": get_state_description(psych) if psych else {},
    }


@router.post("/recover/stimulant")
async def recover_stimulant(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    return await use_stimulant(db, player.id)


@router.post("/recover/sedative")
async def recover_sedative(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    return await use_sedative(db, player.id)


@router.get("/forecast")
async def psych_forecast(
    hours: int = Query(default=24, ge=1, le=168),
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    return await get_psych_forecast(db, player.id, hours)
