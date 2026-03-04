import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.player import PlayerStats
from app.data.skills import SKILL_DEFINITIONS
from app.data.constants import GAME_CONSTANTS


XP_FIELDS = {
    "social": "xp_social",
    "exploitation": "xp_exploitation",
    "cryptography": "xp_cryptography",
    "hardware": "xp_hardware",
    "counterintel": "xp_counterintel",
    "economics": "xp_economics",
}


def get_player_skill_level(stats: PlayerStats, tree: str) -> int:
    field = XP_FIELDS.get(tree)
    if not field:
        return 0
    xp = getattr(stats, field, 0)
    level = xp // GAME_CONSTANTS["XP_PER_LEVEL"]
    return min(level, GAME_CONSTANTS["MAX_SKILL_LEVEL"])


def get_max_skill_level(stats: PlayerStats) -> int:
    return max(get_player_skill_level(stats, tree) for tree in XP_FIELDS)


def get_unlocked_abilities(stats: PlayerStats) -> dict:
    unlocked = {}
    for tree_key, tree_data in SKILL_DEFINITIONS.items():
        level = get_player_skill_level(stats, tree_key)
        tree_abilities = []
        for ability in tree_data["abilities"]:
            if level >= ability["level_required"]:
                tree_abilities.append(ability)
        unlocked[tree_key] = tree_abilities
    return unlocked


async def award_skill_xp(db: AsyncSession, player_id: uuid.UUID, tree: str, amount: int) -> dict:
    result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player_id))
    stats = result.scalar_one_or_none()
    if not stats:
        return {}

    field = XP_FIELDS.get(tree)
    if not field:
        return {}

    old_level = get_player_skill_level(stats, tree)
    current_xp = getattr(stats, field, 0)
    setattr(stats, field, current_xp + amount)
    new_level = min((current_xp + amount) // GAME_CONSTANTS["XP_PER_LEVEL"], GAME_CONSTANTS["MAX_SKILL_LEVEL"])

    await db.commit()

    return {
        "tree": tree,
        "xp_gained": amount,
        "new_xp": current_xp + amount,
        "old_level": old_level,
        "new_level": new_level,
        "leveled_up": new_level > old_level,
    }


def get_operation_modifiers(stats: PlayerStats) -> dict:
    modifiers = {
        "exploit_success_bonus": 0.0,
        "recon_success_bonus": 0.0,
        "persist_success_bonus": 0.0,
        "monetize_success_bonus": 0.0,
        "artifact_reduction": 0.0,
        "opsec_bonus": 0.0,
        "trace_reduction": 0.0,
        "laundering_fee_reduction": 0.0,
        "post_op_wipe": 0,
        "heat_redirect": 0.0,
        "zero_day_chance": 0.0,
        "passive_privacy_coin_per_hour": 0,
    }

    unlocked = get_unlocked_abilities(stats)

    for tree_key, abilities in unlocked.items():
        for ability in abilities:
            bonus = ability.get("operation_bonus", {})
            phase = bonus.get("phase")
            modifier = bonus.get("success_modifier", 0)

            if phase == "exploit":
                modifiers["exploit_success_bonus"] += modifier
            elif phase == "recon":
                modifiers["recon_success_bonus"] += modifier
                if "zero_day_chance" in bonus:
                    modifiers["zero_day_chance"] += bonus["zero_day_chance"]
            elif phase == "persist":
                modifiers["persist_success_bonus"] += modifier

            if bonus.get("all_phases"):
                opsec = bonus.get("opsec_modifier", 0)
                modifiers["opsec_bonus"] += opsec

            if "artifact_reduction" in bonus:
                modifiers["artifact_reduction"] = max(modifiers["artifact_reduction"], bonus["artifact_reduction"])

            if "trace_reduction" in bonus:
                modifiers["trace_reduction"] = max(modifiers["trace_reduction"], bonus["trace_reduction"])

            if "laundering_fee_reduction" in bonus:
                modifiers["laundering_fee_reduction"] = max(
                    modifiers["laundering_fee_reduction"],
                    bonus["laundering_fee_reduction"]
                )

            if "post_op_wipe" in bonus:
                modifiers["post_op_wipe"] += bonus["post_op_wipe"]

            if "heat_redirect" in bonus:
                modifiers["heat_redirect"] = max(modifiers["heat_redirect"], bonus["heat_redirect"])

            if "passive_privacy_coin_per_hour" in bonus:
                modifiers["passive_privacy_coin_per_hour"] += bonus["passive_privacy_coin_per_hour"]

    return modifiers


def get_skill_tree_summary(stats: PlayerStats) -> list[dict]:
    trees = []
    for tree_key, tree_data in SKILL_DEFINITIONS.items():
        level = get_player_skill_level(stats, tree_key)
        xp_field = tree_data["stat_field"]
        xp = getattr(stats, xp_field, 0)
        next_level_xp = (level + 1) * GAME_CONSTANTS["XP_PER_LEVEL"]

        abilities_with_status = []
        for ability in tree_data["abilities"]:
            abilities_with_status.append({
                **ability,
                "unlocked": level >= ability["level_required"],
            })

        trees.append({
            "key": tree_key,
            "name": tree_data["tree_name"],
            "code": tree_data["code"],
            "description": tree_data["description"],
            "level": level,
            "xp": xp,
            "next_level_xp": next_level_xp,
            "abilities": abilities_with_status,
        })
    return trees
