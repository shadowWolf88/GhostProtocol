from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_player
from app.models.player import Player, PlayerStats
from app.services import world_service
from app.services.player_service import get_player_stats
from sqlalchemy import select

router = APIRouter(prefix="/world", tags=["world"])


@router.get("/nodes")
async def list_nodes(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_player_stats(db, player.id)
    nodes = await world_service.get_all_nodes(db)

    from app.services.skill_service import get_max_skill_level
    max_level = get_max_skill_level(stats) if stats else 0

    from app.services.redis_service import get_node_alert_level
    result = []
    for node in nodes:
        alert = await get_node_alert_level(node.node_key)
        result.append({
            "id": str(node.id),
            "node_key": node.node_key,
            "name": node.name,
            "category": node.category,
            "tier": node.tier,
            "vulnerability_score": node.vulnerability_score,
            "is_accessible": world_service._is_node_accessible(node, max_level),
            "alert_level": alert,
        })
    return result


@router.get("/nodes/{node_key}")
async def get_node(
    node_key: str,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    node = await world_service.get_node(db, node_key)
    if not node:
        raise HTTPException(status_code=404, detail="Ghost not found.")
    return node


@router.get("/nodes/{node_key}/intel")
async def node_intel(
    node_key: str,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    stats = await get_player_stats(db, player.id)
    if not stats:
        raise HTTPException(status_code=404, detail="Player stats not found.")

    intel = await world_service.get_node_intel(db, node_key, stats)
    if not intel:
        raise HTTPException(status_code=404, detail="Ghost not found.")

    node = intel["node"]
    return {
        "node_key": node.node_key,
        "name": node.name,
        "category": node.category,
        "tier": node.tier,
        "vulnerability_score": node.vulnerability_score,
        "defender_tier": node.defender_tier,
        "heat_multiplier": node.heat_multiplier,
        "base_crypto_reward": node.base_crypto_reward,
        "base_reputation_reward": node.base_reputation_reward,
        "current_alert_level": intel["current_alert_level"],
        "estimated_success_chance": intel["estimated_success_chance"],
        "recommended_approach": intel["recommended_approach"],
        "risk_assessment": intel["risk_assessment"],
        "defender_profile": intel["defender_profile"],
        "is_accessible": intel["is_accessible"],
    }


@router.get("/map")
async def world_map(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    nodes = await world_service.get_all_nodes(db)
    return world_service.get_world_map(nodes)
