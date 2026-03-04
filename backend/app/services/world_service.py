import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.player import WorldNode, PlayerStats
from app.services.redis_service import get_node_alert_level
from app.services.skill_service import get_max_skill_level
from app.data.constants import GAME_CONSTANTS


def _is_node_accessible(node: WorldNode, max_skill_level: int) -> bool:
    thresholds = {
        1: 0,
        2: GAME_CONSTANTS["NODE_TIER2_SKILL_REQUIRED"],
        3: GAME_CONSTANTS["NODE_TIER3_SKILL_REQUIRED"],
        4: GAME_CONSTANTS["NODE_TIER4_SKILL_REQUIRED"],
        5: GAME_CONSTANTS["NODE_TIER5_SKILL_REQUIRED"],
    }
    required = thresholds.get(node.tier, 999)
    return max_skill_level >= required


async def get_all_nodes(db: AsyncSession) -> list[WorldNode]:
    result = await db.execute(select(WorldNode).where(WorldNode.is_active == True))
    return list(result.scalars().all())


async def get_node(db: AsyncSession, node_key: str) -> WorldNode | None:
    result = await db.execute(select(WorldNode).where(WorldNode.node_key == node_key))
    return result.scalar_one_or_none()


async def get_node_by_id(db: AsyncSession, node_id: uuid.UUID) -> WorldNode | None:
    result = await db.execute(select(WorldNode).where(WorldNode.id == node_id))
    return result.scalar_one_or_none()


async def get_accessible_nodes(db: AsyncSession, stats: PlayerStats) -> list[WorldNode]:
    nodes = await get_all_nodes(db)
    max_level = get_max_skill_level(stats)
    return [n for n in nodes if _is_node_accessible(n, max_level)]


async def get_node_intel(db: AsyncSession, node_key: str, stats: PlayerStats) -> dict:
    node = await get_node(db, node_key)
    if not node:
        return {}

    from app.services.skill_service import get_player_skill_level
    alert_level = await get_node_alert_level(node_key)
    max_level = get_max_skill_level(stats)

    skill_level = max(
        get_player_skill_level(stats, "exploitation"),
        get_player_skill_level(stats, "social"),
        get_player_skill_level(stats, "hardware"),
    )

    base_chance = 0.60
    skill_bonus = (skill_level / 50) * 0.25
    defender_penalty = node.defender_tier * 0.05
    alert_penalty = (alert_level / 100) * 0.20
    vuln_bonus = (node.vulnerability_score / 100) * 0.15

    estimated_chance = base_chance + skill_bonus + vuln_bonus - defender_penalty - alert_penalty
    estimated_chance = max(0.05, min(0.95, estimated_chance))

    if node.category in ("darknet",):
        recommended = "technical"
    elif node.category in ("corporate", "social_media"):
        recommended = "social"
    elif node.category in ("government", "intelligence"):
        recommended = "combined"
    else:
        recommended = "technical"

    if estimated_chance > 0.75:
        risk = "LOW — Target is exposed. Standard approach viable."
    elif estimated_chance > 0.55:
        risk = "MEDIUM — Capable defenders. Precision recommended."
    elif estimated_chance > 0.35:
        risk = "HIGH — Serious opposition. Prepare fallback routes."
    else:
        risk = "CRITICAL — This is a kill box. Approach only if necessary."

    defender_profiles = {
        1: "Automated scanners only. No active defenders.",
        2: "Junior security team. Slow response, limited tooling.",
        3: "Experienced SOC team. Active monitoring, 24/7 coverage.",
        4: "Elite threat hunters. Custom detection. Zero mercy.",
        5: "Nation-state grade. You are already detected. Question is when they move.",
    }

    return {
        "node": node,
        "current_alert_level": alert_level,
        "estimated_success_chance": round(estimated_chance, 3),
        "recommended_approach": recommended,
        "risk_assessment": risk,
        "defender_profile": defender_profiles.get(node.defender_tier, "Unknown"),
        "is_accessible": _is_node_accessible(node, max_level),
    }


async def update_node_vulnerability(db: AsyncSession, node_id: uuid.UUID, delta: int):
    result = await db.execute(select(WorldNode).where(WorldNode.id == node_id))
    node = result.scalar_one_or_none()
    if node:
        node.vulnerability_score = max(0, min(100, node.vulnerability_score + delta))
        await db.commit()


async def patch_all_nodes(db: AsyncSession):
    nodes = await get_all_nodes(db)
    for node in nodes:
        old_vuln = node.vulnerability_score
        node.vulnerability_score = max(0, old_vuln - node.patch_rate)
    await db.commit()


def get_world_map(nodes: list[WorldNode]) -> dict:
    categories = {}
    for node in nodes:
        cat = node.category
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "node_key": node.node_key,
            "name": node.name,
            "tier": node.tier,
            "vulnerability_score": node.vulnerability_score,
        })
    return categories
