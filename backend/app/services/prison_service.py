import uuid
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.player import Player, PlayerStats, Identity, HeatRecord
from app.models.prison import PrisonRecord, PrisonActivity
from app.data.constants import GAME_CONSTANTS


async def trigger_arrest(
    db: AsyncSession, player_id: uuid.UUID, failed_operation
) -> PrisonRecord:
    result = await db.execute(select(Player).where(Player.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise ValueError("Player not found")

    existing = await db.execute(
        select(PrisonRecord).where(
            PrisonRecord.player_id == player_id,
            PrisonRecord.is_active == True,
        )
    )
    if existing.scalar_one_or_none():
        return None

    heat_result = await db.execute(
        select(HeatRecord).where(HeatRecord.player_id == player_id)
    )
    heat_records = list(heat_result.scalars().all())

    federal_heat = next((r.level for r in heat_records if r.domain == "federal"), 0)
    intel_heat = next((r.level for r in heat_records if r.domain == "intelligence"), 0)

    sentence_hours = min(
        GAME_CONSTANTS["PRISON_MAX_HOURS"],
        int(GAME_CONSTANTS["PRISON_BASE_HOURS"] + (federal_heat * 0.5) + (intel_heat * 1.0))
    )

    now = datetime.utcnow()
    charges = [
        "Unauthorized access to protected computer systems",
        "Wire fraud and identity theft",
        "Computer fraud and abuse act violations",
        "Conspiracy to commit computer intrusion",
        "Money laundering and cyber-enabled financial crimes",
    ]
    charge = random.choice(charges)

    prison_record = PrisonRecord(
        player_id=player_id,
        sentence_hours=sentence_hours,
        arrested_at=now,
        release_at=now + timedelta(hours=sentence_hours),
        charge_description=charge,
        is_active=True,
    )
    db.add(prison_record)

    player.is_active = False

    for record in heat_records:
        record.level = 30
        record.updated_at = now

    identities_result = await db.execute(
        select(Identity).where(
            Identity.player_id == player_id,
            Identity.is_burned == False,
        )
    )
    identities = list(identities_result.scalars().all())
    for identity in identities:
        if identity.heat_accumulated > 50:
            identity.is_burned = True
            identity.burned_at = now

    await db.commit()
    return prison_record


async def get_prison_status(db: AsyncSession, player_id: uuid.UUID) -> dict:
    result = await db.execute(
        select(PrisonRecord).where(
            PrisonRecord.player_id == player_id,
            PrisonRecord.is_active == True,
        )
    )
    record = result.scalar_one_or_none()

    if not record:
        return {"in_prison": False, "record": None, "time_remaining_hours": 0.0}

    now = datetime.utcnow()
    if record.release_at <= now:
        await release_player(db, player_id)
        return {"in_prison": False, "record": None, "time_remaining_hours": 0.0}

    time_remaining = (record.release_at - now).total_seconds() / 3600

    return {
        "in_prison": True,
        "record": {
            "id": str(record.id),
            "sentence_hours": record.sentence_hours,
            "arrested_at": record.arrested_at.isoformat(),
            "release_at": record.release_at.isoformat(),
            "charge": record.charge_description,
            "broker_info_count": record.broker_info_count,
            "legal_fight_count": record.legal_fight_count,
            "escaped": record.escaped,
        },
        "time_remaining_hours": round(time_remaining, 2),
    }


async def perform_prison_activity(
    db: AsyncSession, player_id: uuid.UUID, activity_type: str, params: dict
) -> dict:
    prison_result = await db.execute(
        select(PrisonRecord).where(
            PrisonRecord.player_id == player_id,
            PrisonRecord.is_active == True,
        )
    )
    record = prison_result.scalar_one_or_none()
    if not record:
        raise ValueError("Not currently incarcerated")

    stats_result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    stats = stats_result.scalar_one_or_none()

    if activity_type == "broker_info":
        rep_gain = random.randint(50, 200)
        stats.reputation = (stats.reputation or 0) + rep_gain
        record.broker_info_count += 1

        activity = PrisonActivity(
            player_id=player_id,
            activity_type="broker_info",
            description="Traded intelligence on outside operations",
            outcome=f"Earned {rep_gain} reputation with criminal network",
            resolved_at=datetime.utcnow(),
        )
        db.add(activity)
        await db.commit()
        return {"success": True, "rep_gained": rep_gain, "message": f"Information sold. +{rep_gain} dark web reputation."}

    elif activity_type == "recruit_contact":
        cost = 100
        if not stats or stats.crypto < cost:
            raise ValueError("Insufficient crypto for bribes")

        stats.crypto -= cost
        activity = PrisonActivity(
            player_id=player_id,
            activity_type="recruit_contact",
            description="Recruited criminal contact",
            cost_crypto=cost,
            outcome="NPC asset secured for post-release operations",
            resolved_at=datetime.utcnow(),
        )
        db.add(activity)
        await db.commit()
        return {"success": True, "cost": cost, "message": "Contact secured. Asset available post-release."}

    elif activity_type == "escape_plan":
        if record.broker_info_count < 3:
            raise ValueError(f"Need {3 - record.broker_info_count} more broker_info activities first")

        success = random.random() < GAME_CONSTANTS["PRISON_ESCAPE_SUCCESS_CHANCE"]
        if success:
            record.escaped = True
            record.is_active = False
            player_result = await db.execute(select(Player).where(Player.id == player_id))
            player = player_result.scalar_one_or_none()
            if player:
                player.is_active = True
                stats.reputation = (stats.reputation or 0) + 200
            await db.commit()
            return {"success": True, "message": "Escape successful. You're out. Run.", "rep_gained": 200}
        else:
            record.release_at = record.release_at + timedelta(hours=GAME_CONSTANTS["PRISON_ESCAPE_PENALTY_HOURS"])
            record.sentence_hours += GAME_CONSTANTS["PRISON_ESCAPE_PENALTY_HOURS"]
            await db.commit()
            return {"success": False, "message": f"Escape failed. +{GAME_CONSTANTS['PRISON_ESCAPE_PENALTY_HOURS']}h added to sentence."}

    elif activity_type == "legal_fight":
        if record.legal_fight_count >= GAME_CONSTANTS["PRISON_LEGAL_FIGHT_MAX"]:
            raise ValueError("Maximum legal challenges exhausted")

        cost = GAME_CONSTANTS["PRISON_LEGAL_FIGHT_COST"]
        if not stats or stats.crypto < cost:
            raise ValueError("Insufficient crypto for legal fees")

        stats.crypto -= cost
        reduction_hours = int(record.sentence_hours * GAME_CONSTANTS["PRISON_LEGAL_FIGHT_REDUCTION"])
        record.release_at = record.release_at - timedelta(hours=reduction_hours)
        record.sentence_hours -= reduction_hours
        record.legal_fight_count += 1

        activity = PrisonActivity(
            player_id=player_id,
            activity_type="legal_fight",
            description="Filed legal challenge",
            cost_crypto=cost,
            outcome=f"Sentence reduced by {reduction_hours} hours",
            resolved_at=datetime.utcnow(),
        )
        db.add(activity)
        await db.commit()
        return {"success": True, "hours_reduced": reduction_hours, "cost": cost}

    raise ValueError(f"Unknown activity: {activity_type}")


async def release_player(db: AsyncSession, player_id: uuid.UUID) -> dict:
    prison_result = await db.execute(
        select(PrisonRecord).where(
            PrisonRecord.player_id == player_id,
            PrisonRecord.is_active == True,
        )
    )
    record = prison_result.scalar_one_or_none()

    player_result = await db.execute(select(Player).where(Player.id == player_id))
    player = player_result.scalar_one_or_none()

    stats_result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    stats = stats_result.scalar_one_or_none()

    xp_bonus = 0
    if record and player and stats:
        record.is_active = False
        player.is_active = True

        hours_served = record.sentence_hours
        xp_bonus = hours_served * GAME_CONSTANTS["PRISON_TIME_SERVED_XP_PER_HOUR"]
        stats.xp_counterintel += xp_bonus
        await db.commit()

    return {
        "released": True,
        "xp_bonus": xp_bonus,
        "message": "Released. The world doesn't know you yet. Keep it that way.",
    }
