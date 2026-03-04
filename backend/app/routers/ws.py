from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.websocket_manager import manager
from app.core.security import decode_token
import asyncio
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{player_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    player_id: str,
    token: str = Query(...),
):
    payload = decode_token(token)
    if not payload or payload.get("sub") != player_id:
        await websocket.close(code=4001)
        return

    await manager.connect(player_id, websocket)

    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Signal established. You are live.",
        })

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30.0)
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for player {player_id}: {e}")
    finally:
        manager.disconnect(player_id)
