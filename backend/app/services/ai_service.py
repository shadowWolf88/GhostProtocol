import logging
import json
from app.config import settings
from app.services.redis_service import (
    cache_ai_briefing, get_ai_briefing_cache,
    increment_ai_failure_count, reset_ai_failure_count,
    get_ai_circuit_broken, set_ai_circuit_broken,
)

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None and settings.ANTHROPIC_API_KEY:
        import anthropic
        _client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


async def _call_claude(system: str, user: str, max_tokens: int = 256) -> str | None:
    if await get_ai_circuit_broken():
        return None

    client = _get_client()
    if not client:
        return None

    try:
        import anthropic
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        await reset_ai_failure_count()
        return response.content[0].text
    except Exception as e:
        logger.error(f"Anthropic API error: {e}")
        count = await increment_ai_failure_count()
        if count >= 3:
            await set_ai_circuit_broken(300)
            logger.warning("AI circuit breaker triggered — 5 minute cooldown")
        return None


async def generate_mission_briefing(node, approach: str, player_handle: str) -> str:
    node_key = getattr(node, 'node_key', 'unknown')
    cached = await get_ai_briefing_cache(node_key, approach)
    if cached:
        return cached

    system = (
        "You are a terse, paranoid hacker briefing another operative. "
        "Write in second-person present tense. Max 4 sentences. No fluff. "
        "Reference realistic techniques. Never mention real companies or real exploits by CVE number."
    )
    user = (
        f"Generate an operation briefing for infiltrating {node.name}, "
        f"a tier-{node.tier} {node.category} target. Approach: {approach}. "
        f"Operative handle: {player_handle}. Vulnerability score: {node.vulnerability_score}/100."
    )

    result = await _call_claude(system, user)
    if result:
        await cache_ai_briefing(node_key, approach, result, 3600)
        return result

    return (
        f"Target: {node.name}. Tier {node.tier} {node.category}. "
        f"Approach: {approach}. Vulnerability window at {node.vulnerability_score}%. "
        f"Move fast. Leave nothing."
    )


async def generate_npc_response(
    npc_role: str,
    player_message: str,
    social_skill_level: int,
    approach: str,
) -> dict:
    system = (
        f"You are roleplaying as a {npc_role} at a company receiving a suspicious communication. "
        "Respond realistically. Higher player skill means better-crafted approaches. "
        "Return JSON with keys: response (str, 2-3 sentences max), "
        "suspicion_delta (int, -20 to +30), success_probability (float 0.0-1.0). "
        "Be concise and realistic."
    )
    user = (
        f"Social skill level: {social_skill_level}/50. "
        f"Approach: {approach}. "
        f"Player's message/action: {player_message}"
    )

    result = await _call_claude(system, user, max_tokens=300)
    if result:
        try:
            data = json.loads(result)
            return {
                "response": data.get("response", "..."),
                "suspicion_delta": int(data.get("suspicion_delta", 10)),
                "success_probability": float(data.get("success_probability", 0.4)),
            }
        except Exception:
            pass

    return {
        "response": f"I'm not sure what you mean. Could you clarify?",
        "suspicion_delta": 5,
        "success_probability": 0.35 + (social_skill_level / 50) * 0.30,
    }


async def generate_world_event(current_heat_landscape: dict, active_factions: list) -> dict:
    system = (
        "You generate world events for a cyberpunk hacking game. "
        "Events affect the game state. Return JSON with: "
        "headline (str, <80 chars), description (str, 2 sentences), "
        "effect_type (one of: heat_modifier, node_vulnerability_change, market_price_shift, faction_event), "
        "effect_data (dict with relevant numbers). Be dramatic but grounded."
    )
    user = f"Generate a world event. Global heat landscape: {current_heat_landscape}. Active factions: {active_factions}"

    result = await _call_claude(system, user, max_tokens=400)
    if result:
        try:
            return json.loads(result)
        except Exception:
            pass

    events = [
        {
            "headline": "INTERPOL Issues Global APT Advisory",
            "description": "Law enforcement agencies worldwide share threat intelligence on active intrusion campaigns. Corporate networks have elevated defensive posture.",
            "effect_type": "heat_modifier",
            "effect_data": {"federal_decay_multiplier": 0.7, "duration_hours": 4},
        },
        {
            "headline": "Major Cloud Provider Suffers Credential Breach",
            "description": "A leaked credential database floods the dark web. Corporate authentication systems are temporarily weakened.",
            "effect_type": "node_vulnerability_change",
            "effect_data": {"category": "corporate", "vulnerability_delta": 15, "duration_hours": 6},
        },
        {
            "headline": "Dark Market 'ShadowBazaar' Seized by Authorities",
            "description": "Coordinated law enforcement action takes down a major marketplace. Prices spike as supply tightens.",
            "effect_type": "market_price_shift",
            "effect_data": {"price_multiplier": 1.4, "categories": ["exploit", "identity_package"]},
        },
    ]

    import random
    return random.choice(events)


async def generate_operation_debrief(
    operation,
    success: bool,
    artifacts_left: list,
    heat_gained: int,
) -> str:
    system = (
        "You write terse operation debriefs for a cyberpunk hacking game. "
        "Max 4 sentences. Second-person. Gritty, realistic. "
        "Highlight what went well, what left traces, what the heat means."
    )

    node_name = operation.phase_data.get("node_name", "the target")
    phases = operation.phase_data.get("phases_completed", [])

    user = (
        f"Operation against {node_name}. "
        f"Success: {success}. Phases completed: {phases}. "
        f"Artifacts left: {len(artifacts_left)}. Heat gained: {heat_gained}."
    )

    result = await _call_claude(system, user)
    if result:
        return result

    if success:
        artifact_note = f" {len(artifacts_left)} trace(s) left behind — clean them." if artifacts_left else " Unusually clean exit."
        return (
            f"Operation against {node_name} complete. Phases: {', '.join(phases) if phases else 'none'}. "
            f"Heat delta: +{heat_gained}.{artifact_note}"
        )
    return f"Operation failed. {node_name} resisted. Heat: +{heat_gained}. Review your approach and regroup."
