from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_player
from app.models.player import Player
from app.services.onboarding_service import (
    get_onboarding, check_onboarding_trigger, get_phantom_hint,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.get("/state")
async def onboarding_state(player: Player = Depends(get_current_player)):
    return await get_onboarding(player.id)


@router.post("/check")
async def check_trigger(
    body: dict,
    player: Player = Depends(get_current_player),
):
    event = body.get("event", "")
    return await check_onboarding_trigger(player.id, event)


@router.get("/hint")
async def hint(player: Player = Depends(get_current_player)):
    hint_text = await get_phantom_hint(player.id)
    return {
        "sender": "PHANTOM",
        "message": f"PHANTOM: {hint_text}",
    }
