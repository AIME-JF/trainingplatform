"""WebSocket 连接管理"""
import json
from typing import Dict, Set

from fastapi import WebSocket
from logger import logger

# 连接池：training_id -> set of WebSocket connections
_connections: Dict[int, Set[WebSocket]] = {}


async def connect(training_id: int, websocket: WebSocket):
    await websocket.accept()
    if training_id not in _connections:
        _connections[training_id] = set()
    _connections[training_id].add(websocket)
    logger.info(f"WS connected: training={training_id}, total={len(_connections[training_id])}")


def disconnect(training_id: int, websocket: WebSocket):
    if training_id in _connections:
        _connections[training_id].discard(websocket)
        if not _connections[training_id]:
            del _connections[training_id]


async def broadcast_activity(training_id: int, activity_data: dict):
    """广播动态到所有连接该培训班的客户端"""
    connections = _connections.get(training_id, set())
    if not connections:
        return
    message = json.dumps(activity_data, ensure_ascii=False, default=str)
    dead = []
    for ws in connections:
        try:
            await ws.send_text(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connections.discard(ws)
