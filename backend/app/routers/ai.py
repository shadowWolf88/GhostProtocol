from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, get_current_player
from app.models.player import Player
from app.services import ai_service, world_service
from app.services.player_service import get_player_stats
from app.services.skill_service import get_player_skill_level

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/briefing/{node_key}")
async def get_briefing(
    node_key: str,
    approach: str = "technical",
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    node = await world_service.get_node(db, node_key)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found.")
    briefing = await ai_service.generate_mission_briefing(node, approach, player.handle)
    return {"node_key": node_key, "approach": approach, "briefing": briefing}


@router.post("/npc-interaction")
async def npc_interaction(
    body: dict,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    npc_role = body.get("npc_role", "IT administrator")
    message = body.get("message", "")
    approach = body.get("approach", "email")

    stats = await get_player_stats(db, player.id)
    social_level = get_player_skill_level(stats, "social") if stats else 0

    return await ai_service.generate_npc_response(npc_role, message, social_level, approach)


@router.get("/world-event")
async def world_event(player: Player = Depends(get_current_player)):
    from app.services.heat_service import DOMAIN_DECAY_RATES
    from app.data.factions import FACTION_DATA
    event = await ai_service.generate_world_event(
        {"domains": list(DOMAIN_DECAY_RATES.keys())},
        list(FACTION_DATA.keys()),
    )
    return event
