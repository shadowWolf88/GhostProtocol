from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_db, get_current_player
from app.models.player import Player
from app.models.prison import PrisonActivity
from app.services.prison_service import get_prison_status, perform_prison_activity, release_player

router = APIRouter(prefix="/prison", tags=["prison"])

AVAILABLE_ACTIVITIES = [
    {
        "type": "broker_info",
        "name": "Broker Information",
        "description": "Trade intelligence on outside operations. Earn dark web reputation.",
        "cost": 0,
        "requirements": None,
    },
    {
        "type": "recruit_contact",
        "name": "Recruit Contact",
        "description": "Cultivate a criminal contact for post-release asset use.",
        "cost": 100,
        "requirements": None,
    },
    {
        "type": "escape_plan",
        "name": "Escape Attempt",
        "description": "20% chance of immediate release. Failure adds 24h to sentence.",
        "cost": 0,
        "requirements": "3 broker_info activities",
    },
    {
        "type": "legal_fight",
        "name": "Legal Challenge",
        "description": "Hire a lawyer. Reduce sentence by 20%. Max 3 challenges.",
        "cost": 500,
        "requirements": None,
    },
]


@router.get("/status")
async def prison_status(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    return await get_prison_status(db, player.id)


@router.get("/activities")
async def available_activities(player: Player = Depends(get_current_player)):
    return AVAILABLE_ACTIVITIES


@router.post("/activity")
async def do_activity(
    body: dict,
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    activity_type = body.get("activity_type")
    if not activity_type:
        raise HTTPException(status_code=400, detail="activity_type required")

    try:
        return await perform_prison_activity(db, player.id, activity_type, body.get("params", {}))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
async def prison_history(
    player: Player = Depends(get_current_player),
    db: AsyncSession = Depends(get_db),
):
    from app.models.prison import PrisonRecord
    result = await db.execute(
        select(PrisonRecord)
        .where(PrisonRecord.player_id == player.id)
        .order_by(PrisonRecord.arrested_at.desc())
    )
    records = list(result.scalars().all())
    return [
        {
            "id": str(r.id),
            "sentence_hours": r.sentence_hours,
            "arrested_at": r.arrested_at.isoformat(),
            "release_at": r.release_at.isoformat(),
            "charge": r.charge_description,
            "escaped": r.escaped,
            "is_active": r.is_active,
        }
        for r in records
    ]
