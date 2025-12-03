# backend/gateway/publisher.py
import asyncio
import json
from collections import deque
from typing import Set

class Broadcaster:
    """
    Simple fan-out with a small replay buffer so reconnecting clients
    get context. Messages are JSON strings.
    """
    def __init__(self, replay_size: int = 200, replay_on_join: int = 10):
        self._subs: Set = set()
        self._ring = deque(maxlen=replay_size)
        self._lock = asyncio.Lock()
        self._replay_on_join = replay_on_join

    async def add(self, ws):
        await ws.accept()
        async with self._lock:
            self._subs.add(ws)
            # light replay
            for msg in list(self._ring)[-self._replay_on_join:]:
                await ws.send_text(msg)

    async def discard(self, ws):
        async with self._lock:
            self._subs.discard(ws)

    async def publish_json(self, payload: dict):
        msg = json.dumps(payload, separators=(",", ":"))
        async with self._lock:
            self._ring.append(msg)
            dead = []
            for ws in list(self._subs):
                try:
                    await ws.send_text(msg)
                except Exception:
                    dead.append(ws)
            for d in dead:
                self._subs.discard(d)

# Singleton broadcaster used by gRPC servicers and the WS app
broadcaster = Broadcaster()