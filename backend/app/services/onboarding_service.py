import uuid
from app.services.redis_service import get_onboarding_state, set_onboarding_state

ONBOARDING_STEPS = [
    "handler_intro",
    "first_node_scan",
    "first_operation",
    "first_market_buy",
    "heat_explained",
]

PHANTOM_HINTS = [
    "You're overthinking it. Run the operation. Clean up the mess after.",
    "Your trace graph is getting complicated. Maybe rotate identities.",
    "Heat doesn't go away by ignoring it. Go dark or deal with the consequences.",
    "Skills compound. Don't neglect cryptography — it's what separates operators from amateurs.",
    "The market has things you need. Most players ignore it. Don't be most players.",
]

PHANTOM_MESSAGES = {
    "handler_intro": (
        "PHANTOM: Signal established. You're new. That's not a problem yet.\n"
        "You have a device. You have crypto. You have time.\n"
        "Start small — find a target. Scan it. Learn its vulnerabilities.\n"
        "Type: NODES\n"
        "Don't be stupid."
    ),
    "first_node_scan": (
        "PHANTOM: Good. You've identified a target.\n"
        "Intel is everything. The operation lives or dies in recon.\n"
        "Pick a Tier 1 target. Learn the terrain.\n"
        "Type: OP NEW {node_key} technical"
    ),
    "first_operation": (
        "PHANTOM: You ran an operation. Whatever happened, you learned something.\n"
        "Check your trace artifacts. Understand what you left behind.\n"
        "And check your heat. That number matters more than you think.\n"
        "Type: TRACE"
    ),
    "first_market_buy": (
        "PHANTOM: You bought something. Good.\n"
        "The market is your force multiplier. Tools make operators.\n"
        "Learn what's available. Some items will change how you operate.\n"
        "The paranoia suppressants are popular for a reason."
    ),
    "heat_explained": (
        "PHANTOM: Your heat is climbing. Pay attention to it.\n"
        "Intelligence domain heat decays the slowest — 0.5 points per hour.\n"
        "Local LEO forgets in hours. They never forget.\n"
        "Go dark when you need to. The game rewards patience."
    ),
}

EVENT_TO_STEP = {
    "registered": "handler_intro",
    "first_scan": "first_node_scan",
    "operation_complete": "first_operation",
    "market_buy": "first_market_buy",
    "heat_increased": "heat_explained",
}


async def get_onboarding(player_id: uuid.UUID) -> dict:
    state = await get_onboarding_state(str(player_id))
    if state is None:
        state = {"completed": [], "current_step": "handler_intro"}
        await set_onboarding_state(str(player_id), state)

    completed = state.get("completed", [])
    total = len(ONBOARDING_STEPS)
    done = len(completed)

    return {
        "completed": completed,
        "current_step": state.get("current_step"),
        "completion_percentage": round(done / total * 100),
        "all_steps": ONBOARDING_STEPS,
    }


async def check_onboarding_trigger(player_id: uuid.UUID, event: str) -> dict | None:
    step = EVENT_TO_STEP.get(event)
    if not step:
        return None

    state = await get_onboarding_state(str(player_id))
    if state is None:
        state = {"completed": [], "current_step": "handler_intro"}

    completed = state.get("completed", [])
    if step in completed:
        return None

    completed.append(step)
    next_idx = ONBOARDING_STEPS.index(step) + 1
    next_step = ONBOARDING_STEPS[next_idx] if next_idx < len(ONBOARDING_STEPS) else None

    state["completed"] = completed
    state["current_step"] = next_step
    await set_onboarding_state(str(player_id), state)

    message = PHANTOM_MESSAGES.get(step, "")
    return {
        "step": step,
        "message": message,
        "next_step": next_step,
    }


async def get_phantom_hint(player_id: uuid.UUID) -> str:
    import random
    return random.choice(PHANTOM_HINTS)
