import json
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, player_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[player_id] = websocket
        logger.info(f"Player {player_id} connected via WebSocket")

    def disconnect(self, player_id: str):
        self.active_connections.pop(player_id, None)
        logger.info(f"Player {player_id} disconnected")

    async def send_to_player(self, player_id: str, message: dict):
        ws = self.active_connections.get(player_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(player_id)

    async def broadcast(self, message: dict):
        disconnected = []
        for player_id, ws in self.active_connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(player_id)
        for pid in disconnected:
            self.disconnect(pid)

    def is_connected(self, player_id: str) -> bool:
        return player_id in self.active_connections


manager = ConnectionManager()
