from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_player
from app.models.player import Player
from app.services.faction_service import (
    get_player_faction_relations, get_faction_intro_message,
    initiate_faction_join, check_faction_contact_eligibility,
)
from app.services.player_service import get_player_stats
from app.data.factions import FACTION_DATA

router = APIRouter(prefix="/factions", tags=["factions"])


@router.get("")
async def all_factions(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    return await get_player_faction_relations(db, player.id)


@router.get("/{faction_key}")
async def faction_detail(
    faction_key: str,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    if faction_key not in FACTION_DATA:
        raise HTTPException(status_code=404, detail="Faction not found.")
    relations = await get_player_faction_relations(db, player.id)
    faction_rel = next((r for r in relations if r["faction_key"] == faction_key), None)
    return faction_rel


@router.get("/{faction_key}/contact")
async def faction_contact(
    faction_key: str,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_player_stats(db, player.id)
    faction = FACTION_DATA.get(faction_key)
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found.")

    if not stats or stats.reputation < faction["contact_threshold"]:
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient reputation. Need {faction['contact_threshold']} to be contacted."
        )

    return await get_faction_intro_message(faction_key, player.handle)


@router.post("/{faction_key}/join")
async def join_faction(
    faction_key: str,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    if faction_key not in FACTION_DATA:
        raise HTTPException(status_code=404, detail="Faction not found.")
    try:
        return await initiate_faction_join(db, player.id, faction_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
