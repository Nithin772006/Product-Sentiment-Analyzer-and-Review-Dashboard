"""
app/api/routes/realtime.py
──────────────────────────
WebSocket endpoint and ConnectionManager to broadcast real-time scraper/NLP processing events.
"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.utils.logger import logger

router = APIRouter(prefix="/realtime", tags=["realtime"])


class ConnectionManager:
    """Manages active WebSocket client connections for real-time broadcasts."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("New WebSocket client connected. Active connections: {n}", n=len(self.active_connections))

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket client disconnected. Active connections: {n}", n=len(self.active_connections))

    async def broadcast(self, message: dict) -> None:
        """Broadcast JSON message to all connected clients."""
        logger.info("Broadcasting WebSocket event: {msg}", msg=message)
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.error("Failed to send WebSocket message: {exc}", exc=exc)
                # Cleanup dead connection
                self.disconnect(connection)


# Singleton connection manager instance
manager = ConnectionManager()


@router.websocket("")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket route endpoint for real-time logs and notifications."""
    await manager.connect(websocket)
    try:
        # Keep connection open and listen for client heartbeats/messages
        while True:
            data = await websocket.receive_text()
            # Respond to ping
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        logger.error("WebSocket connection error: {exc}", exc=exc)
        manager.disconnect(websocket)
