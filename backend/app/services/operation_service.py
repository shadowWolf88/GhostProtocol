import uuid
import random
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.player import (
    Player, PlayerStats, PsychState, Device, WorldNode,
    Operation, TraceArtifact, HeatRecord, Identity,
)
from app.schemas.operations import PhaseOutcome, OperationResult, OperationCreate
from app.services import skill_service, narrative_service, heat_service, psych_service
from app.services.redis_service import increment_node_alert
from app.data.constants import GAME_CONSTANTS

PHASE_ORDER = ["recon", "exploit", "persist", "monetize"]

BASE_SUCCESS_RATES = {
    "recon": 0.85,
    "exploit": 0.60,
    "persist": 0.70,
    "monetize": 0.75,
}

ARTIFACT_TYPES_BY_PHASE = {
    "recon": ["timing_pattern", "ip_leak"],
    "exploit": ["log_entry", "device_fingerprint"],
    "persist": ["log_entry", "identity_overlap"],
    "monetize": ["ip_leak", "timing_pattern", "identity_overlap"],
}

BASE_ARTIFACT_CHANCES = {
    "recon": 0.20,
    "exploit": 0.50,
    "persist": 0.40,
    "monetize": 0.30,
}

PHASE_XP_AWARDS = {
    "recon": {"social": 50},
    "exploit": {"exploitation": 150},
    "persist": {"counterintel": 100},
    "monetize": {"economics": 100},
}

PHASE_HEAT_ON_SUCCESS = {
    "recon": GAME_CONSTANTS["HEAT_RECON_SUCCESS"],
    "exploit": GAME_CONSTANTS["HEAT_EXPLOIT_SUCCESS"],
    "persist": GAME_CONSTANTS["HEAT_PERSIST_SUCCESS"],
    "monetize": GAME_CONSTANTS["HEAT_MONETIZE_SUCCESS"],
}


async def _get_node(db: AsyncSession, node_key: str) -> WorldNode | None:
    result = await db.execute(select(WorldNode).where(WorldNode.node_key == node_key))
    return result.scalar_one_or_none()


def _calculate_success_chance(
    phase: str,
    node: WorldNode,
    stats: PlayerStats,
    psych_mods: dict,
    skill_mods: dict,
    alert_level: int,
    device: Device,
) -> float:
    base = BASE_SUCCESS_RATES[phase]
    skill_level = max(
        skill_service.get_player_skill_level(stats, "exploitation"),
        skill_service.get_player_skill_level(stats, "social"),
        skill_service.get_player_skill_level(stats, "hardware"),
    )

    phase_bonuses = {
        "recon": skill_mods.get("recon_success_bonus", 0),
        "exploit": skill_mods.get("exploit_success_bonus", 0),
        "persist": skill_mods.get("persist_success_bonus", 0),
        "monetize": 0,
    }

    chance = (
        base
        + (skill_level / 50) * 0.25
        + phase_bonuses.get(phase, 0)
        + skill_mods.get("opsec_bonus", 0)
        - (node.defender_tier * 0.05)
        - (alert_level / 100) * 0.20
        + (1 - device.forensic_trace_level / 100) * 0.10
        - psych_mods.get("stress_penalty", 0)
        - psych_mods.get("sleep_penalty", 0)
        - psych_mods.get("burnout_penalty", 0)
        + psych_mods.get("ego_bonus", 0)
        + psych_mods.get("focus_bonus", 0)
        + psych_mods.get("paranoia_bonus_opsec", 0)
    )

    cascade = psych_mods.get("cascade_risk", 0)
    if cascade > 0 and random.random() < cascade:
        chance -= 0.30

    return max(0.05, min(0.95, chance))


def _generate_artifacts(
    phase: str,
    node: WorldNode,
    stats: PlayerStats,
    skill_mods: dict,
    operation_id: uuid.UUID,
    player_id: uuid.UUID,
    device: Device,
    identity_id: uuid.UUID | None,
) -> list[TraceArtifact]:
    artifact_types = ARTIFACT_TYPES_BY_PHASE[phase]
    base_chance = BASE_ARTIFACT_CHANCES[phase]

    reduction = skill_mods.get("artifact_reduction", 0)
    heat_mult = node.heat_multiplier

    effective_chance = base_chance * (1 - reduction) * heat_mult
    artifacts = []

    if random.random() < effective_chance:
        artifact_type = random.choice(artifact_types)
        severity = random.randint(1, min(10, node.tier * 2 + 1))

        artifact = TraceArtifact(
            player_id=player_id,
            operation_id=operation_id,
            artifact_type=artifact_type,
            description=narrative_service.generate_artifact_description(
                artifact_type, {"node": node.name}
            ),
            node_id=node.id,
            device_id=device.id,
            identity_id=identity_id,
            severity=severity,
        )
        artifacts.append(artifact)

    return artifacts


async def create_operation(
    db: AsyncSession,
    player: Player,
    data: OperationCreate,
) -> Operation:
    stats_result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player.id))
    stats = stats_result.scalar_one_or_none()

    if not stats or stats.energy < GAME_CONSTANTS["OPERATION_ENERGY_COST"]:
        raise ValueError("Insufficient energy. Rest before operating.")

    node = await _get_node(db, data.node_key)
    if not node:
        raise ValueError(f"Node '{data.node_key}' not found.")

    device_result = await db.execute(
        select(Device).where(Device.id == data.device_id, Device.player_id == player.id)
    )
    device = device_result.scalar_one_or_none()
    if not device or device.is_destroyed or device.is_compromised:
        raise ValueError("Device unavailable. Use a clean device.")

    stats.energy -= GAME_CONSTANTS["OPERATION_ENERGY_COST"]

    briefing = ""
    try:
        from app.services.ai_service import generate_mission_briefing
        briefing = await generate_mission_briefing(node, data.approach, player.handle)
    except Exception:
        briefing = f"Target: {node.name}. Approach: {data.approach}. Proceed."

    op = Operation(
        player_id=player.id,
        node_id=node.id,
        device_id=data.device_id,
        identity_id=data.identity_id,
        approach=data.approach,
        status="recon",
        phase_data={
            "briefing": briefing,
            "phases_completed": [],
            "phase_results": [],
            "node_key": data.node_key,
            "node_name": node.name,
            "node_category": node.category,
            "node_tier": node.tier,
        },
    )
    db.add(op)
    await db.commit()
    await db.refresh(op)
    return op


async def advance_operation(
    db: AsyncSession,
    operation: Operation,
    player: Player,
    action: str,
    parameters: dict,
    ws_manager=None,
) -> PhaseOutcome:
    current_phase = operation.status
    if current_phase not in PHASE_ORDER:
        raise ValueError("Operation is not in an advanceable state.")

    stats_result = await db.execute(select(PlayerStats).where(PlayerStats.player_id == player.id))
    stats = stats_result.scalar_one_or_none()

    psych_result = await db.execute(select(PsychState).where(PsychState.player_id == player.id))
    psych = psych_result.scalar_one_or_none()

    device_result = await db.execute(select(Device).where(Device.id == operation.device_id))
    device = device_result.scalar_one_or_none()

    node_result = await db.execute(select(WorldNode).where(WorldNode.id == operation.node_id))
    node = node_result.scalar_one_or_none()

    from app.services.redis_service import get_node_alert_level
    alert_level = await get_node_alert_level(operation.phase_data.get("node_key", ""))

    psych_mods = await psych_service.apply_psych_consequences(db, player.id)
    skill_mods = skill_service.get_operation_modifiers(stats)

    success_chance = _calculate_success_chance(
        current_phase, node, stats, psych_mods, skill_mods, alert_level, device
    )
    success = random.random() < success_chance

    artifacts = _generate_artifacts(
        current_phase, node, stats, skill_mods,
        operation.id, player.id, device, operation.identity_id,
    )

    for artifact in artifacts:
        db.add(artifact)

    heat_amount = 0
    if success:
        base_heat = PHASE_HEAT_ON_SUCCESS.get(current_phase, 10)
        heat_amount = int(base_heat * node.heat_multiplier * (1 - skill_mods.get("heat_redirect", 0)))
    else:
        heat_amount = int(GAME_CONSTANTS["HEAT_FAILURE_MULTIPLIER"] * node.heat_multiplier)

    await heat_service.add_heat(db, player.id, "federal", heat_amount, ws_manager)
    if node.category in ("government", "infrastructure"):
        await heat_service.add_heat(db, player.id, "intelligence", heat_amount // 2, ws_manager)
    await heat_service.add_heat(db, player.id, "corporate", heat_amount // 3, ws_manager)

    await increment_node_alert(operation.phase_data.get("node_key", ""), heat_amount // 2)

    xp_partial = {}
    if success:
        xp_map = PHASE_XP_AWARDS.get(current_phase, {})
        for tree, amount in xp_map.items():
            result = await skill_service.award_skill_xp(db, player.id, tree, amount)
            xp_partial[tree] = amount

    narrative = narrative_service.generate_phase_narrative(
        current_phase, success, node, operation.approach,
        [a.artifact_type for a in artifacts], player.handle,
    )

    phase_result = {
        "phase": current_phase,
        "success": success,
        "heat_generated": heat_amount,
        "artifacts": [str(a.id) for a in artifacts],
        "xp": xp_partial,
    }

    phase_data = dict(operation.phase_data)
    phase_results = phase_data.get("phase_results", [])
    phase_results.append(phase_result)
    phase_data["phase_results"] = phase_results

    phases_completed = phase_data.get("phases_completed", [])
    if success:
        phases_completed.append(current_phase)
    phase_data["phases_completed"] = phases_completed

    current_idx = PHASE_ORDER.index(current_phase)
    next_phase = PHASE_ORDER[current_idx + 1] if current_idx < len(PHASE_ORDER) - 1 else "complete"
    next_phase_unlocked = success

    if success and next_phase != "complete":
        operation.status = next_phase
    elif next_phase == "complete" and success:
        operation.status = "complete"
        operation.completed_at = datetime.utcnow()
        await _finalize_operation(db, operation, player, stats, phase_results, node)
    elif not success and current_phase == "exploit":
        operation.status = "failed"
        operation.fail_reason = "Exploit phase failed"
        operation.completed_at = datetime.utcnow()
    elif not success:
        phase_data["last_phase_failed"] = True

    operation.phase_data = phase_data
    operation.heat_generated += heat_amount
    operation.artifacts_left = [str(a.id) for a in artifacts] + operation.artifacts_left

    await db.commit()

    await psych_service.update_psych_after_operation(db, player.id, [phase_result])

    if ws_manager:
        await ws_manager.send_to_player(str(player.id), {
            "type": "operation_update",
            "operation_id": str(operation.id),
            "phase": current_phase,
            "success": success,
            "status": operation.status,
            "message": narrative[:100],
        })

    heat_status = await heat_service.get_player_heat(db, player.id)
    if heat_status.threat_tier == 5 and not success:
        from app.services.prison_service import trigger_arrest
        await trigger_arrest(db, player.id, operation)

    return PhaseOutcome(
        phase=current_phase,
        success=success,
        narrative=narrative,
        artifacts_generated=[a.artifact_type for a in artifacts],
        xp_partial=xp_partial,
        heat_generated=heat_amount,
        next_phase_unlocked=next_phase_unlocked,
        can_abort=success and next_phase != "complete",
        next_phase=next_phase if success else None,
    )


async def _finalize_operation(
    db: AsyncSession,
    operation: Operation,
    player: Player,
    stats: PlayerStats,
    phase_results: list[dict],
    node: WorldNode,
):
    phases_done = [p["phase"] for p in phase_results if p.get("success")]
    crypto_earned = 0
    rep_earned = 0

    if "monetize" in phases_done:
        tier_min = GAME_CONSTANTS.get(f"TIER{node.tier}_CRYPTO_MIN", 50)
        tier_max = GAME_CONSTANTS.get(f"TIER{node.tier}_CRYPTO_MAX", 150)
        crypto_earned = random.randint(tier_min, tier_max)
        rep_earned = node.base_reputation_reward

        stats.crypto += crypto_earned
        stats.reputation += rep_earned

    operation.crypto_earned = crypto_earned
    operation.reputation_earned = rep_earned

    node.last_breached_at = datetime.utcnow()

    from app.services.ai_service import generate_operation_debrief
    try:
        debrief = await generate_operation_debrief(operation, True, operation.artifacts_left, operation.heat_generated)
    except Exception:
        debrief = narrative_service.generate_operation_result_narrative(
            "complete", node, player.handle, phases_done
        )

    phase_data = dict(operation.phase_data)
    phase_data["debrief"] = debrief
    operation.phase_data = phase_data

    from app.services.graph_service import get_neo4j_driver, record_operation_in_graph
    try:
        driver = get_neo4j_driver()
        artifact_result = await db.execute(
            select(TraceArtifact).where(TraceArtifact.operation_id == operation.id)
        )
        artifacts = list(artifact_result.scalars().all())

        operation.node_key = node.node_key
        operation.node_name = node.name
        operation.node_category = node.category
        operation.node_tier = node.tier

        await record_operation_in_graph(driver, operation, artifacts)
    except Exception:
        pass

    from app.services.faction_service import check_initiation_completion
    await check_initiation_completion(db, player.id, operation)


async def abort_operation(db: AsyncSession, operation: Operation, player: Player) -> dict:
    phase_data = dict(operation.phase_data)
    phases_completed = phase_data.get("phases_completed", [])
    phase_results = phase_data.get("phase_results", [])

    partial_xp = {}
    for phase in phases_completed:
        for tree, amount in PHASE_XP_AWARDS.get(phase, {}).items():
            xp_amount = amount // 2
            await skill_service.award_skill_xp(db, player.id, tree, xp_amount)
            partial_xp[tree] = partial_xp.get(tree, 0) + xp_amount

    heat_on_abort = operation.heat_generated // 2
    await heat_service.add_heat(db, player.id, "federal", heat_on_abort)

    operation.status = "aborted"
    operation.completed_at = datetime.utcnow()
    operation.fail_reason = "Voluntarily aborted"
    operation.xp_awarded = partial_xp

    await db.commit()
    await psych_service.update_psych_after_operation(db, player.id, phase_results)

    return {
        "operation_id": str(operation.id),
        "status": "aborted",
        "phases_completed": phases_completed,
        "partial_xp": partial_xp,
        "message": "Operation aborted. Partial extraction complete. Stay dark for a while.",
    }


async def get_operation_result(db: AsyncSession, operation: Operation) -> OperationResult:
    phase_data = operation.phase_data or {}
    return OperationResult(
        operation_id=operation.id,
        status=operation.status,
        xp_awarded=operation.xp_awarded or {},
        crypto_earned=operation.crypto_earned,
        reputation_earned=operation.reputation_earned,
        artifacts_left=operation.artifacts_left or [],
        heat_generated=operation.heat_generated,
        narrative=phase_data.get("debrief", "Operation complete."),
        phases_completed=phase_data.get("phases_completed", []),
    )
