from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_player
from app.models.player import Player
from app.services.skill_service import (
    get_skill_tree_summary, get_operation_modifiers,
    get_unlocked_abilities, get_player_skill_level,
)
from app.services.player_service import get_player_stats
from app.data.skills import SKILL_DEFINITIONS

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("")
async def all_skills(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_player_stats(db, player.id)
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found.")
    return get_skill_tree_summary(stats)


@router.get("/modifiers")
async def skill_modifiers(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_player_stats(db, player.id)
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found.")
    return get_operation_modifiers(stats)


@router.get("/abilities/unlocked")
async def unlocked_abilities(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_player_stats(db, player.id)
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found.")
    return get_unlocked_abilities(stats)


@router.get("/{tree}")
async def tree_detail(
    tree: str,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    if tree not in SKILL_DEFINITIONS:
        raise HTTPException(status_code=404, detail=f"Skill tree '{tree}' not found.")
    stats = await get_player_stats(db, player.id)
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found.")

    level = get_player_skill_level(stats, tree)
    tree_data = SKILL_DEFINITIONS[tree]
    xp_field = tree_data["stat_field"]
    xp = getattr(stats, xp_field, 0)

    abilities = [
        {**a, "unlocked": level >= a["level_required"]}
        for a in tree_data["abilities"]
    ]

    return {
        "key": tree,
        "name": tree_data["tree_name"],
        "code": tree_data["code"],
        "description": tree_data["description"],
        "level": level,
        "xp": xp,
        "abilities": abilities,
    }
