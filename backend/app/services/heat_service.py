import uuid
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.player import HeatRecord
from app.schemas.heat import HeatStatus, HeatDomain
from app.services.redis_service import (
    get_go_dark, set_player_surveillance, clear_go_dark
)
from app.data.constants import GAME_CONSTANTS

DOMAIN_DECAY_RATES = {
    "local_leo": GAME_CONSTANTS["DECAY_LOCAL_LEO"],
    "federal": GAME_CONSTANTS["DECAY_FEDERAL"],
    "intelligence": GAME_CONSTANTS["DECAY_INTELLIGENCE"],
    "corporate": GAME_CONSTANTS["DECAY_CORPORATE"],
    "rivals": GAME_CONSTANTS["DECAY_RIVALS"],
}

HEAT_WEIGHTS = {
    "local_leo": GAME_CONSTANTS["HEAT_WEIGHT_LOCAL_LEO"],
    "federal": GAME_CONSTANTS["HEAT_WEIGHT_FEDERAL"],
    "intelligence": GAME_CONSTANTS["HEAT_WEIGHT_INTELLIGENCE"],
    "corporate": GAME_CONSTANTS["HEAT_WEIGHT_CORPORATE"],
    "rivals": GAME_CONSTANTS["HEAT_WEIGHT_RIVALS"],
}

THREAT_TIERS = {
    1: {"max": 20, "name": "Off The Radar", "description": "Normal operations. No active interest."},
    2: {"max": 40, "name": "Person of Interest", "description": "Random checks. Low-level surveillance."},
    3: {"max": 60, "name": "Active Investigation", "description": "They're building a file on you."},
    4: {"max": 80, "name": "Raid Imminent", "description": "Safe houses compromised. Ops risky."},
    5: {"max": 100, "name": "Arrest Probable", "description": "One failure and you're inside."},
}


def _calculate_decay(level: float, decay_rate: float, hours_elapsed: float, dark_multiplier: float = 1.0) -> float:
    total_decay = decay_rate * hours_elapsed * dark_multiplier
    return max(0.0, level - total_decay)


def _get_threat_tier(total_heat: float) -> int:
    if total_heat <= 20:
        return 1
    elif total_heat <= 40:
        return 2
    elif total_heat <= 60:
        return 3
    elif total_heat <= 80:
        return 4
    return 5


async def get_player_heat(db: AsyncSession, player_id: uuid.UUID) -> HeatStatus:
    result = await db.execute(select(HeatRecord).where(HeatRecord.player_id == player_id))
    records = list(result.scalars().all())

    now = datetime.utcnow()
    domains = {}

    go_dark_ts = await get_go_dark(str(player_id))
    is_dark = go_dark_ts is not None and go_dark_ts > now.timestamp()
    dark_multiplier = GAME_CONSTANTS["GO_DARK_DECAY_MULTIPLIER"] if is_dark else 1.0

    for domain, decay_rate in DOMAIN_DECAY_RATES.items():
        record = next((r for r in records if r.domain == domain), None)
        if record:
            hours_elapsed = (now - record.updated_at).total_seconds() / 3600
            decayed_level = _calculate_decay(record.level, decay_rate, hours_elapsed, dark_multiplier)
            domains[domain] = HeatDomain(
                domain=domain,
                level=int(decayed_level),
                decay_rate=decay_rate,
                last_incident_at=record.last_incident_at,
            )
        else:
            domains[domain] = HeatDomain(
                domain=domain,
                level=0,
                decay_rate=decay_rate,
                last_incident_at=None,
            )

    total_heat = sum(
        domains[d].level * HEAT_WEIGHTS[d]
        for d in HEAT_WEIGHTS
    )

    threat_tier = _get_threat_tier(total_heat)
    tier_info = THREAT_TIERS[threat_tier]

    hours_to_safe = 0.0
    if total_heat > 20:
        hours_to_safe = (total_heat - 20) / max(
            sum(DOMAIN_DECAY_RATES[d] * HEAT_WEIGHTS[d] for d in HEAT_WEIGHTS), 0.1
        )

    go_dark_until = None
    if go_dark_ts:
        go_dark_until = datetime.fromtimestamp(go_dark_ts)

    return HeatStatus(
        player_id=player_id,
        domains=domains,
        total_heat=round(total_heat, 2),
        threat_tier=threat_tier,
        threat_tier_name=tier_info["name"],
        threat_description=tier_info["description"],
        is_dark_web_burned=domains.get("rivals", HeatDomain(domain="rivals", level=0, decay_rate=3.0, last_incident_at=None)).level > 70,
        estimated_time_to_decay_safe=round(hours_to_safe, 1),
        go_dark_until=go_dark_until,
    )


async def add_heat(
    db: AsyncSession,
    player_id: uuid.UUID,
    domain: str,
    amount: int,
    ws_manager=None,
) -> HeatStatus:
    result = await db.execute(
        select(HeatRecord).where(
            HeatRecord.player_id == player_id,
            HeatRecord.domain == domain,
        )
    )
    record = result.scalar_one_or_none()
    now = datetime.utcnow()

    if record:
        hours_elapsed = (now - record.updated_at).total_seconds() / 3600
        decayed = _calculate_decay(record.level, DOMAIN_DECAY_RATES[domain], hours_elapsed)
        record.level = min(100, int(decayed) + amount)
        record.last_incident_at = now
        record.updated_at = now
    else:
        record = HeatRecord(
            player_id=player_id,
            domain=domain,
            level=min(100, amount),
            decay_rate=DOMAIN_DECAY_RATES[domain],
            last_incident_at=now,
            updated_at=now,
        )
        db.add(record)

    await db.commit()

    heat_status = await get_player_heat(db, player_id)

    if heat_status.threat_tier >= 4:
        await set_player_surveillance(str(player_id), True)

    if ws_manager:
        await ws_manager.send_to_player(str(player_id), {
            "type": "heat_update",
            "domain": domain,
            "new_level": heat_status.domains[domain].level,
            "threat_tier": heat_status.threat_tier,
            "threat_tier_name": heat_status.threat_tier_name,
        })

    return heat_status


async def decay_all_heat(db: AsyncSession, player_id: uuid.UUID):
    result = await db.execute(select(HeatRecord).where(HeatRecord.player_id == player_id))
    records = list(result.scalars().all())
    now = datetime.utcnow()

    go_dark_ts = await get_go_dark(str(player_id))
    is_dark = go_dark_ts is not None and go_dark_ts > now.timestamp()
    dark_multiplier = GAME_CONSTANTS["GO_DARK_DECAY_MULTIPLIER"] if is_dark else 1.0

    for record in records:
        hours_elapsed = (now - record.updated_at).total_seconds() / 3600
        record.level = int(_calculate_decay(record.level, DOMAIN_DECAY_RATES[record.domain], hours_elapsed, dark_multiplier))
        record.updated_at = now

    await db.commit()


async def go_dark(db: AsyncSession, player_id: uuid.UUID, hours: int) -> dict:
    import time
    from app.services.redis_service import set_go_dark as redis_set_go_dark
    now = datetime.utcnow()
    until_ts = (now + timedelta(hours=hours)).timestamp()
    await redis_set_go_dark(str(player_id), until_ts)

    current = await get_player_heat(db, player_id)
    projected = {}
    for domain, heat_domain in current.domains.items():
        decay_rate = DOMAIN_DECAY_RATES[domain]
        projected_level = _calculate_decay(
            heat_domain.level, decay_rate, hours,
            GAME_CONSTANTS["GO_DARK_DECAY_MULTIPLIER"]
        )
        projected[domain] = int(projected_level)

    return {
        "message": f"Signal dark. Comms suspended for {hours} hours.",
        "go_dark_until": datetime.fromtimestamp(until_ts).isoformat(),
        "projected_heat_after": projected,
    }


async def get_heat_decay_preview(db: AsyncSession, player_id: uuid.UUID, hours: int) -> dict:
    current = await get_player_heat(db, player_id)
    projected = {}

    go_dark_ts = await get_go_dark(str(player_id))
    now = datetime.utcnow().timestamp()
    is_dark = go_dark_ts is not None and go_dark_ts > now
    dark_multiplier = GAME_CONSTANTS["GO_DARK_DECAY_MULTIPLIER"] if is_dark else 1.0

    for domain, heat_domain in current.domains.items():
        decay_rate = DOMAIN_DECAY_RATES[domain]
        projected_level = _calculate_decay(heat_domain.level, decay_rate, hours, dark_multiplier)
        projected[domain] = int(projected_level)

    projected_total = sum(projected[d] * HEAT_WEIGHTS[d] for d in HEAT_WEIGHTS)
    projected_tier = _get_threat_tier(projected_total)

    return {
        "hours": hours,
        "current": {d: heat_domain.level for d, heat_domain in current.domains.items()},
        "projected": projected,
        "current_total": current.total_heat,
        "projected_total": round(projected_total, 2),
        "current_tier": current.threat_tier,
        "projected_tier": projected_tier,
    }
