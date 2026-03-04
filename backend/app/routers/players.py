from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_player
from app.models.player import Player
from app.schemas.player import PlayerPublicProfile, PlayerStatsSchema, PsychStateSchema, DeviceSchema
from app.services.player_service import get_player_by_handle, get_player_stats, get_player_psych, get_player_devices

router = APIRouter(prefix="/players", tags=["players"])


@router.get("/{handle}", response_model=PlayerPublicProfile)
async def get_public_profile(handle: str, db: AsyncSession = Depends(get_db)):
    player = await get_player_by_handle(db, handle)
    if not player:
        raise HTTPException(status_code=404, detail="Ghost not found.")
    stats = await get_player_stats(db, player.id)
    return PlayerPublicProfile(
        handle=player.handle,
        reputation=stats.reputation if stats else 0,
        created_at=player.created_at,
    )


@router.get("/me/stats", response_model=PlayerStatsSchema)
async def my_stats(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_player_stats(db, player.id)
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found.")
    return PlayerStatsSchema.model_validate(stats)


@router.get("/me/psych", response_model=PsychStateSchema)
async def my_psych(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    psych = await get_player_psych(db, player.id)
    if not psych:
        raise HTTPException(status_code=404, detail="Psych state not found.")
    return PsychStateSchema.model_validate(psych)


@router.get("/me/devices")
async def my_devices(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    devices = await get_player_devices(db, player.id)
    return [DeviceSchema.model_validate(d) for d in devices]
