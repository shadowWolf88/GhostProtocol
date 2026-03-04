import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.routers import auth, players, world, skills, operations, heat, trace, psych, economy, ai, factions, prison, onboarding, ws

logger = logging.getLogger(__name__)
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


async def _background_tasks():
    from app.database import AsyncSessionFactory
    from app.services.world_service import patch_all_nodes
    from app.services.redis_service import get_node_alert_level, set_node_alert_level, get_redis
    from app.services.heat_service import decay_all_heat
    from app.services.psych_service import decay_paranoia
    from app.services.faction_service import check_faction_contact_eligibility
    from app.services.ai_service import generate_world_event
    from app.core.websocket_manager import manager
    from app.models.player import Player
    from sqlalchemy import select

    world_event_counter = 0

    while True:
        try:
            async with AsyncSessionFactory() as db:
                await patch_all_nodes(db)

                result = await db.execute(select(Player).where(Player.is_active == True).limit(100))
                active_players = list(result.scalars().all())

                for player in active_players:
                    try:
                        await decay_all_heat(db, player.id)
                        await decay_paranoia(db, player.id)
                        newly_eligible = await check_faction_contact_eligibility(db, player.id)
                        for faction_key in newly_eligible:
                            await manager.send_to_player(str(player.id), {
                                "type": "faction_contact",
                                "faction_key": faction_key,
                                "message": f"A faction has taken notice of your work.",
                            })
                    except Exception as e:
                        logger.debug(f"Background task error for player {player.id}: {e}")

            world_event_counter += 1
            if world_event_counter >= 120:
                world_event_counter = 0
                try:
                    from app.data.factions import FACTION_DATA
                    event = await generate_world_event({}, list(FACTION_DATA.keys()))
                    await manager.broadcast({
                        "type": "world_event",
                        "headline": event.get("headline", "World event"),
                        "description": event.get("description", ""),
                        "effect_type": event.get("effect_type", ""),
                    })
                except Exception as e:
                    logger.debug(f"World event generation failed: {e}")

        except Exception as e:
            logger.error(f"Background task loop error: {e}")

        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Ghost Protocol API starting...")

    try:
        from app.services.graph_service import get_neo4j_driver, init_graph_schema
        driver = get_neo4j_driver()
        await init_graph_schema(driver)
        logger.info("Neo4j graph schema initialized")
    except Exception as e:
        logger.warning(f"Neo4j initialization failed (non-fatal): {e}")

    try:
        from app.utils.seed import run_seed
        await run_seed()
    except Exception as e:
        logger.warning(f"Seed failed (non-fatal): {e}")

    bg_task = asyncio.create_task(_background_tasks())
    logger.info("Background tasks started")

    yield

    bg_task.cancel()
    try:
        await bg_task
    except asyncio.CancelledError:
        pass

    try:
        from app.services.graph_service import close_driver
        await close_driver()
    except Exception:
        pass

    logger.info("Ghost Protocol API shutdown complete")


app = FastAPI(
    title="Ghost Protocol API",
    description="You are not a player. You are an operator.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(422)
async def validation_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Invalid signal. Check your parameters.",
            "errors": str(exc),
        },
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    logger.error(f"Server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "System failure. This incident has been logged."},
    )


@app.get("/health")
async def health():
    return {"status": "online", "codename": "GHOST PROTOCOL"}


PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(players.router, prefix=PREFIX)
app.include_router(world.router, prefix=PREFIX)
app.include_router(skills.router, prefix=PREFIX)
app.include_router(operations.router, prefix=PREFIX)
app.include_router(heat.router, prefix=PREFIX)
app.include_router(trace.router, prefix=PREFIX)
app.include_router(psych.router, prefix=PREFIX)
app.include_router(economy.router, prefix=PREFIX)
app.include_router(ai.router, prefix=PREFIX)
app.include_router(factions.router, prefix=PREFIX)
app.include_router(prison.router, prefix=PREFIX)
app.include_router(onboarding.router, prefix=PREFIX)
app.include_router(ws.router)
