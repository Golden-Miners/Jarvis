"""SSE (Server-Sent Events) support with named events and reconnection."""
import asyncio
import json
import time
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from sse_starlette.sse import EventSourceResponse


class SSEManager:
    """Manages SSE connections and event broadcasting."""

    def __init__(self) -> None:
        self._connections: dict[str, asyncio.Queue[dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, client_id: str) -> asyncio.Queue[dict[str, Any]]:
        """Register a new SSE connection."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
        async with self._lock:
            self._connections[client_id] = queue
        return queue

    async def disconnect(self, client_id: str) -> None:
        """Remove an SSE connection."""
        async with self._lock:
            self._connections.pop(client_id, None)

    async def broadcast(self, event_type: str, data: dict[str, Any]) -> None:
        """Broadcast an event to all connected clients."""
        event = {
            "event": event_type,
            "data": json.dumps(data),
        }
        async with self._lock:
            dead_connections = []
            for client_id, queue in self._connections.items():
                try:
                    queue.put_nowait(event)
                except asyncio.QueueFull:
                    dead_connections.append(client_id)
            for client_id in dead_connections:
                self._connections.pop(client_id, None)

    async def event_generator(
        self, request: Request, client_id: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Generate SSE events for a client."""
        queue = await self.connect(client_id)
        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({"client_id": client_id, "status": "connected"}),
            }
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event
                except TimeoutError:
                    # Send keepalive
                    yield {
                        "event": "keepalive",
                        "data": json.dumps({"ts": datetime.now(UTC).isoformat()}),
                    }
        finally:
            await self.disconnect(client_id)


sse_manager = SSEManager()


async def sse_endpoint(request: Request) -> EventSourceResponse:
    """SSE endpoint for real-time updates."""
    client_id = f"client_{int(time.time() * 1000)}"
    return EventSourceResponse(sse_manager.event_generator(request, client_id))


# Convenience functions for broadcasting specific event types
async def broadcast_signal_created(signal: dict[str, Any]) -> None:
    await sse_manager.broadcast("signal.created", signal)


async def broadcast_signal_updated(signal: dict[str, Any]) -> None:
    await sse_manager.broadcast("signal.updated", signal)


async def broadcast_cycle_status(cycle: dict[str, Any]) -> None:
    await sse_manager.broadcast("cycle.status", cycle)


async def broadcast_agent_health(agent: dict[str, Any]) -> None:
    await sse_manager.broadcast("agent.health", agent)