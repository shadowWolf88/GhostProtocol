import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.player import PsychState
from app.services.redis_service import (
    get_stimulant_boost, set_stimulant_boost,
    get_sedative_penalty, set_sedative_penalty,
)
from app.data.constants import GAME_CONSTANTS


def _clamp(value: int, min_val: int = 0, max_val: int = 100) -> int:
    return max(min_val, min(max_val, value))


def _recalculate_focus(psych: PsychState) -> int:
    focus = 100 - (psych.stress * 0.3) - (psych.sleep_debt * 0.4) - (psych.burnout * 0.3)
    return _clamp(int(focus))


async def update_psych_after_operation(
    db: AsyncSession,
    player_id: uuid.UUID,
    phase_results: list[dict],
):
    result = await db.execute(select(PsychState).where(PsychState.player_id == player_id))
    psych = result.scalar_one_or_none()
    if not psych:
        return

    phases_attempted = len(phase_results)
    phases_failed = sum(1 for p in phase_results if not p.get("success", True))
    total_heat = sum(p.get("heat_generated", 0) for p in phase_results)
    operation_success = phases_attempted >= 4 and phases_failed == 0

    psych.stress = _clamp(psych.stress + (GAME_CONSTANTS["PSYCH_STRESS_PER_PHASE"] * phases_attempted))
    if phases_failed > 0:
        psych.stress = _clamp(psych.stress + 10)
    if total_heat > 30:
        psych.stress = _clamp(psych.stress + 15)

    psych.sleep_debt = _clamp(psych.sleep_debt + (GAME_CONSTANTS["PSYCH_SLEEP_DEBT_PER_PHASE"] * phases_attempted))
    psych.burnout = _clamp(psych.burnout + GAME_CONSTANTS["PSYCH_BURNOUT_PER_OP"])

    if operation_success:
        psych.ego = _clamp(psych.ego + 10)
        psych.trust_index = _clamp(psych.trust_index + 5)
    elif any(p.get("phase") == "exploit" and not p.get("success", True) for p in phase_results):
        psych.ego = _clamp(psych.ego - 10)
        psych.trust_index = _clamp(psych.trust_index - 2)
    elif phases_attempted < 4:
        psych.ego = _clamp(psych.ego - 5)

    psych.paranoia = _clamp(psych.paranoia + int(total_heat * 0.5))
    psych.focus = _recalculate_focus(psych)
    psych.last_updated = datetime.utcnow()

    await db.commit()


async def apply_psych_consequences(db: AsyncSession, player_id: uuid.UUID) -> dict:
    result = await db.execute(select(PsychState).where(PsychState.player_id == player_id))
    psych = result.scalar_one_or_none()
    if not psych:
        return {}

    stim_boost = await get_stimulant_boost(str(player_id))
    sed_penalty = await get_sedative_penalty(str(player_id))

    effective_focus = _clamp(psych.focus + stim_boost - sed_penalty)
    effective_stress = psych.stress
    effective_sleep = psych.sleep_debt

    stress_penalty = 0.10 if effective_stress > 70 else 0.0
    sleep_penalty = 0.15 if effective_sleep > 60 else (0.07 if effective_sleep > 40 else 0.0)
    burnout_penalty = 0.20 if psych.burnout > 80 else (0.10 if psych.burnout > 60 else 0.0)
    ego_bonus = 0.05 if psych.ego > 80 else 0.0
    focus_bonus = 0.08 if effective_focus > 70 else 0.0
    paranoia_opsec = 0.10 if psych.paranoia > 60 else (0.05 if psych.paranoia > 40 else 0.0)

    has_threat_hallucination = psych.paranoia > 80 and psych.sleep_debt > 60
    cascade_risk = 0.05 if psych.burnout > 80 and psych.sleep_debt > 70 else 0.0

    return {
        "stress_penalty": stress_penalty,
        "sleep_penalty": sleep_penalty,
        "burnout_penalty": burnout_penalty,
        "ego_bonus": ego_bonus,
        "focus_bonus": focus_bonus,
        "paranoia_bonus_opsec": paranoia_opsec,
        "has_threat_hallucination": has_threat_hallucination,
        "cascade_risk": cascade_risk,
        "effective_focus": effective_focus,
    }


def get_state_description(psych: PsychState) -> dict:
    def describe(val, labels):
        for threshold, label in sorted(labels, reverse=True):
            if val >= threshold:
                return label
        return labels[-1][1]

    return {
        "stress": {
            "value": psych.stress,
            "label": describe(psych.stress, [(81, "Breaking"), (61, "Strained"), (31, "Elevated"), (0, "Clear")]),
        },
        "paranoia": {
            "value": psych.paranoia,
            "label": describe(psych.paranoia, [(81, "Unraveling"), (51, "Paranoid"), (21, "Cautious"), (0, "Naive")]),
        },
        "sleep_debt": {
            "value": psych.sleep_debt,
            "label": describe(psych.sleep_debt, [(81, "Collapsing"), (61, "Exhausted"), (31, "Fatigued"), (0, "Rested")]),
        },
        "ego": {
            "value": psych.ego,
            "label": describe(psych.ego, [(81, "Reckless"), (61, "Confident"), (31, "Measured"), (0, "Broken")]),
        },
        "burnout": {
            "value": psych.burnout,
            "label": describe(psych.burnout, [(81, "Cascading"), (61, "Burned"), (31, "Worn"), (0, "Fresh")]),
        },
        "trust_index": {
            "value": psych.trust_index,
            "label": describe(psych.trust_index, [(81, "Open"), (51, "Guarded"), (21, "Suspicious"), (0, "Paranoid")]),
        },
        "focus": {
            "value": psych.focus,
            "label": describe(psych.focus, [(81, "Locked"), (51, "Present"), (21, "Scattered"), (0, "Gone")]),
        },
    }


async def go_dark_recovery(db: AsyncSession, player_id: uuid.UUID, hours: int):
    result = await db.execute(select(PsychState).where(PsychState.player_id == player_id))
    psych = result.scalar_one_or_none()
    if not psych:
        return

    psych.stress = _clamp(psych.stress - hours * 3)
    psych.sleep_debt = _clamp(psych.sleep_debt - hours * 5)
    psych.paranoia = _clamp(psych.paranoia - hours * 2)
    psych.burnout = _clamp(psych.burnout - hours * 1)
    psych.focus = _recalculate_focus(psych)
    psych.last_updated = datetime.utcnow()
    await db.commit()


async def use_stimulant(db: AsyncSession, player_id: uuid.UUID) -> dict:
    result = await db.execute(select(PsychState).where(PsychState.player_id == player_id))
    psych = result.scalar_one_or_none()
    if not psych:
        return {}

    psych.stress = _clamp(psych.stress + 10)
    psych.stimulant_dependency = _clamp(psych.stimulant_dependency + 5)
    await set_stimulant_boost(str(player_id), 20, ttl=14400)

    dependency_warning = psych.stimulant_dependency > 60
    psych.last_updated = datetime.utcnow()
    await db.commit()

    return {
        "focus_boost": 20,
        "stress_increase": 10,
        "dependency": psych.stimulant_dependency,
        "dependency_warning": dependency_warning,
        "message": "Stimulant active. Focus enhanced. 4 hour duration." + (
            " WARNING: High dependency. Withdrawal risk." if dependency_warning else ""
        ),
    }


async def use_sedative(db: AsyncSession, player_id: uuid.UUID) -> dict:
    result = await db.execute(select(PsychState).where(PsychState.player_id == player_id))
    psych = result.scalar_one_or_none()
    if not psych:
        return {}

    psych.paranoia = _clamp(psych.paranoia - 30)
    psych.sleep_debt = _clamp(psych.sleep_debt - 20)
    psych.sedative_dependency = _clamp(psych.sedative_dependency + 5)
    await set_sedative_penalty(str(player_id), 15, ttl=21600)

    dependency_warning = psych.sedative_dependency > 60
    psych.last_updated = datetime.utcnow()
    await db.commit()

    return {
        "paranoia_reduction": 30,
        "sleep_debt_reduction": 20,
        "focus_penalty": 15,
        "dependency": psych.sedative_dependency,
        "dependency_warning": dependency_warning,
        "message": "Sedative active. Paranoia suppressed. Focus degraded for 6 hours." + (
            " WARNING: High dependency." if dependency_warning else ""
        ),
    }


async def decay_paranoia(db: AsyncSession, player_id: uuid.UUID):
    result = await db.execute(select(PsychState).where(PsychState.player_id == player_id))
    psych = result.scalar_one_or_none()
    if psych:
        psych.paranoia = _clamp(psych.paranoia - 2)
        psych.focus = _recalculate_focus(psych)
        psych.last_updated = datetime.utcnow()
        await db.commit()


async def get_psych_forecast(db: AsyncSession, player_id: uuid.UUID, hours: int = 24) -> dict:
    result = await db.execute(select(PsychState).where(PsychState.player_id == player_id))
    psych = result.scalar_one_or_none()
    if not psych:
        return {}

    projected_paranoia = _clamp(psych.paranoia - (2 * (hours // 0.5)))
    projected_focus = _clamp(
        100 - (psych.stress * 0.3) - (psych.sleep_debt * 0.4) - (psych.burnout * 0.3)
    )

    return {
        "hours": hours,
        "projected": {
            "stress": psych.stress,
            "paranoia": projected_paranoia,
            "sleep_debt": psych.sleep_debt,
            "ego": psych.ego,
            "burnout": psych.burnout,
            "focus": projected_focus,
        },
        "recommendation": _get_psych_recommendation(psych),
    }


def _get_psych_recommendation(psych: PsychState) -> str:
    if psych.burnout > 70 or psych.sleep_debt > 70:
        return "GO DARK — You are approaching cascade failure. Rest immediately."
    elif psych.stress > 70:
        return "Reduce operation tempo. Your judgment is compromised."
    elif psych.paranoia > 80:
        return "High paranoia is distorting threat assessment. Consider sedatives."
    elif psych.focus < 30:
        return "Focus is critical. Stimulants advised for precision operations."
    else:
        return "Psychological state nominal. Continue operations."
