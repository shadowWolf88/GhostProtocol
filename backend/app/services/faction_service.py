import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.player import PlayerStats, PlayerFactionRelation, Operation
from app.data.factions import FACTION_DATA
from app.services.redis_service import (
    set_faction_contact_notified, get_faction_contact_notified
)


async def get_player_faction_relations(db: AsyncSession, player_id: uuid.UUID) -> list[dict]:
    result = await db.execute(
        select(PlayerFactionRelation).where(PlayerFactionRelation.player_id == player_id)
    )
    relations = {r.faction_key: r for r in result.scalars().all()}

    output = []
    for faction_key, faction_data in FACTION_DATA.items():
        relation = relations.get(faction_key)
        output.append({
            "faction_key": faction_key,
            "name": faction_data["name"],
            "philosophy": faction_data["philosophy"],
            "specialty": faction_data["specialty"],
            "contact_threshold": faction_data["contact_threshold"],
            "join_threshold": faction_data["join_threshold"],
            "standing": relation.standing if relation else 0,
            "is_member": relation.is_member if relation else False,
            "color": faction_data.get("color", "#888888"),
            "bonuses": faction_data["faction_bonuses"],
            "penalties": faction_data["faction_penalties"],
        })
    return output


async def check_faction_contact_eligibility(
    db: AsyncSession, player_id: uuid.UUID
) -> list[str]:
    stats_result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    stats = stats_result.scalar_one_or_none()
    if not stats:
        return []

    eligible = []
    for faction_key, faction_data in FACTION_DATA.items():
        if stats.reputation >= faction_data["contact_threshold"]:
            already_notified = await get_faction_contact_notified(str(player_id), faction_key)
            if not already_notified:
                eligible.append(faction_key)
                await set_faction_contact_notified(str(player_id), faction_key)
    return eligible


async def get_faction_intro_message(
    faction_key: str, player_handle: str
) -> dict:
    faction = FACTION_DATA.get(faction_key)
    if not faction:
        return {}

    contact = faction["npc_contact"]
    return {
        "faction_key": faction_key,
        "faction_name": faction["name"],
        "handle": contact["handle"],
        "flavor": contact["flavor"],
        "message": contact["intro_message"].replace("{handle}", player_handle),
        "join_threshold": faction["join_threshold"],
    }


async def apply_faction_bonuses(
    faction_key: str, operation_modifiers: dict
) -> dict:
    faction = FACTION_DATA.get(faction_key)
    if not faction:
        return operation_modifiers

    bonuses = faction.get("faction_bonuses", {})
    mods = dict(operation_modifiers)

    if "recon_success" in bonuses:
        mods["recon_success_bonus"] = mods.get("recon_success_bonus", 0) + bonuses["recon_success"]
    if "monetize_success" in bonuses:
        mods["monetize_success_bonus"] = mods.get("monetize_success_bonus", 0) + bonuses["monetize_success"]

    return mods


async def initiate_faction_join(
    db: AsyncSession, player_id: uuid.UUID, faction_key: str
) -> dict:
    stats_result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    stats = stats_result.scalar_one_or_none()

    faction = FACTION_DATA.get(faction_key)
    if not faction:
        raise ValueError("Unknown faction")

    if not stats or stats.reputation < faction["join_threshold"]:
        raise ValueError(f"Insufficient reputation. Need {faction['join_threshold']}.")

    rel_result = await db.execute(
        select(PlayerFactionRelation).where(
            PlayerFactionRelation.player_id == player_id,
            PlayerFactionRelation.faction_key == faction_key,
        )
    )
    relation = rel_result.scalar_one_or_none()
    if not relation:
        relation = PlayerFactionRelation(
            player_id=player_id,
            faction_key=faction_key,
            standing=0,
        )
        db.add(relation)

    relation.standing = max(relation.standing, 10)
    await db.commit()

    return {
        "faction_key": faction_key,
        "faction_name": faction["name"],
        "status": "initiation_pending",
        "initiation_mission_type": faction["initiation_mission_type"],
        "message": f"Initiation accepted. Complete a {faction['initiation_mission_type']} operation to prove yourself.",
    }


async def check_initiation_completion(
    db: AsyncSession, player_id: uuid.UUID, operation: Operation
) -> bool:
    relations_result = await db.execute(
        select(PlayerFactionRelation).where(
            PlayerFactionRelation.player_id == player_id,
            PlayerFactionRelation.is_member == False,
            PlayerFactionRelation.standing > 0,
        )
    )
    pending_relations = list(relations_result.scalars().all())

    for relation in pending_relations:
        faction = FACTION_DATA.get(relation.faction_key)
        if not faction:
            continue

        required_type = faction["initiation_mission_type"]
        if required_type == "any" or operation.status == "complete":
            relation.is_member = True
            relation.standing = 50
            relation.joined_at = datetime.utcnow()
            await db.commit()
            return True

    return False


async def update_faction_standing(
    db: AsyncSession, player_id: uuid.UUID, faction_key: str, delta: int
):
    result = await db.execute(
        select(PlayerFactionRelation).where(
            PlayerFactionRelation.player_id == player_id,
            PlayerFactionRelation.faction_key == faction_key,
        )
    )
    relation = result.scalar_one_or_none()
    if relation:
        relation.standing = max(-100, min(100, relation.standing + delta))
        await db.commit()
