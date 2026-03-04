from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_player
from app.models.player import Player
from app.services.heat_service import (
    get_player_heat, go_dark, get_heat_decay_preview
)

router = APIRouter(prefix="/heat", tags=["heat"])


@router.get("")
async def heat_status(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    return await get_player_heat(db, player.id)


@router.get("/preview")
async def heat_preview(
    hours: int = Query(default=24, ge=1, le=168),
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    return await get_heat_decay_preview(db, player.id, hours)


@router.post("/go-dark")
async def initiate_go_dark(
    hours: int = Query(default=8, ge=1, le=72),
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    result = await go_dark(db, player.id, hours)

    from app.services.psych_service import go_dark_recovery
    await go_dark_recovery(db, player.id, hours)

    return result


@router.get("/threat-tier")
async def threat_tier(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    heat = await get_player_heat(db, player.id)
    return {
        "tier": heat.threat_tier,
        "name": heat.threat_tier_name,
        "description": heat.threat_description,
        "total_heat": heat.total_heat,
    }
