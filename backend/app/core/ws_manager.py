"""
Real-time notification delivery over WebSocket. This is purely an
additive delivery layer — notifications are still created and stored
via services/notification_service.py exactly as before; this module
only pushes them instantly to whoever's actively connected.

If a recipient isn't connected, nothing is lost — they just see the
notification next time they call GET /notifications/mine (REST,
in api/notifications_ws.py... note: despite the shared filename with
that REST file per the original scaffold, this is a separate concern
kept in the same file for now since they're small).
"""

import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError

from app.core.security import decode_token


class ConnectionManager:
    """
    Simple in-memory map of user_id -> active WebSocket connection.
    Adequate for a single-server deployment (which is what DIAZO runs
    on per PROJECT_SPEC.md — one Render service, not a multi-instance
    cluster) — a multi-server setup would need a shared store (e.g.
    Redis pub/sub) instead, which is out of scope here.
    """

    def __init__(self):
        self.active_connections: dict[uuid.UUID, WebSocket] = {}

    async def connect(self, user_id: uuid.UUID, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: uuid.UUID):
        self.active_connections.pop(user_id, None)

    async def push_to_user(self, user_id: uuid.UUID, payload: dict):
        """Called by notification_service.py after saving a
        notification. Silently does nothing if the user isn't
        currently connected — that's the expected, non-error case."""
        connection = self.active_connections.get(user_id)
        if connection:
            await connection.send_text(json.dumps(payload))


manager = ConnectionManager()

ws_router = APIRouter()


@ws_router.websocket("/ws/notifications")
async def notifications_websocket(websocket: WebSocket, token: str = Query(...)):
    """
    Client connects with their JWT as a query param (WebSocket
    connections can't send custom headers the way REST requests can,
    so this is the standard workaround): ws://.../ws/notifications?token=<access_token>
    """
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        await websocket.close(code=4001)  # custom code: invalid auth
        return

    user_id = uuid.UUID(payload["sub"])
    await manager.connect(user_id, websocket)

    try:
        while True:
            # This endpoint is push-only from the server's side; we
            # still need to await something to detect disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id)