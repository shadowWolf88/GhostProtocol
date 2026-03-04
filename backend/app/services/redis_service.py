import json
import redis.asyncio as aioredis
from app.config import settings

_redis_client: aioredis.Redis | None = None


def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


async def set_node_alert_level(node_key: str, level: int, ttl_seconds: int = 3600):
    r = get_redis()
    await r.setex(f"alert:{node_key}", ttl_seconds, str(max(0, min(100, level))))


async def get_node_alert_level(node_key: str) -> int:
    r = get_redis()
    val = await r.get(f"alert:{node_key}")
    return int(val) if val else 0


async def increment_node_alert(node_key: str, amount: int):
    r = get_redis()
    key = f"alert:{node_key}"
    current = await get_node_alert_level(node_key)
    new_val = min(100, current + amount)
    await r.setex(key, 3600, str(new_val))


async def decay_node_alert(node_key: str, amount: int = 5):
    r = get_redis()
    current = await get_node_alert_level(node_key)
    if current > 0:
        new_val = max(0, current - amount)
        await r.setex(f"alert:{node_key}", 3600, str(new_val))


async def set_player_session(player_id: str, data: dict, ttl: int = 86400):
    r = get_redis()
    await r.setex(f"session:{player_id}", ttl, json.dumps(data))


async def get_player_session(player_id: str) -> dict | None:
    r = get_redis()
    val = await r.get(f"session:{player_id}")
    return json.loads(val) if val else None


async def set_go_dark(player_id: str, until_ts: float):
    r = get_redis()
    await r.set(f"dark:{player_id}", str(until_ts))


async def get_go_dark(player_id: str) -> float | None:
    r = get_redis()
    val = await r.get(f"dark:{player_id}")
    return float(val) if val else None


async def clear_go_dark(player_id: str):
    r = get_redis()
    await r.delete(f"dark:{player_id}")


async def set_player_surveillance(player_id: str, value: bool = True, ttl: int = 86400):
    r = get_redis()
    if value:
        await r.setex(f"surveillance:{player_id}", ttl, "1")
    else:
        await r.delete(f"surveillance:{player_id}")


async def get_player_surveillance(player_id: str) -> bool:
    r = get_redis()
    return bool(await r.get(f"surveillance:{player_id}"))


async def set_onboarding_state(player_id: str, state: dict):
    r = get_redis()
    await r.set(f"onboarding:{player_id}", json.dumps(state))


async def get_onboarding_state(player_id: str) -> dict | None:
    r = get_redis()
    val = await r.get(f"onboarding:{player_id}")
    return json.loads(val) if val else None


async def set_faction_contact_notified(player_id: str, faction_key: str):
    r = get_redis()
    await r.set(f"faction_notified:{player_id}:{faction_key}", "1")


async def get_faction_contact_notified(player_id: str, faction_key: str) -> bool:
    r = get_redis()
    return bool(await r.get(f"faction_notified:{player_id}:{faction_key}"))


async def cache_ai_briefing(node_key: str, approach: str, briefing: str, ttl: int = 3600):
    r = get_redis()
    await r.setex(f"briefing:{node_key}:{approach}", ttl, briefing)


async def get_ai_briefing_cache(node_key: str, approach: str) -> str | None:
    r = get_redis()
    return await r.get(f"briefing:{node_key}:{approach}")


async def set_stimulant_boost(player_id: str, boost: int, ttl: int = 14400):
    r = get_redis()
    await r.setex(f"stimulant:{player_id}", ttl, str(boost))


async def get_stimulant_boost(player_id: str) -> int:
    r = get_redis()
    val = await r.get(f"stimulant:{player_id}")
    return int(val) if val else 0


async def set_sedative_penalty(player_id: str, penalty: int, ttl: int = 21600):
    r = get_redis()
    await r.setex(f"sedative:{player_id}", ttl, str(penalty))


async def get_sedative_penalty(player_id: str) -> int:
    r = get_redis()
    val = await r.get(f"sedative:{player_id}")
    return int(val) if val else 0


async def increment_ai_failure_count() -> int:
    r = get_redis()
    count = await r.incr("ai:failure_count")
    await r.expire("ai:failure_count", 300)
    return count


async def reset_ai_failure_count():
    r = get_redis()
    await r.delete("ai:failure_count")


async def get_ai_circuit_broken() -> bool:
    r = get_redis()
    return bool(await r.get("ai:circuit_broken"))


async def set_ai_circuit_broken(ttl: int = 300):
    r = get_redis()
    await r.setex("ai:circuit_broken", ttl, "1")
