# ws_manager.py
import asyncio
from fastapi import WebSocket
from typing import Dict, Set

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.loop = None

    def set_event_loop(self, loop):
        self.loop = loop

    async def connect(self, websocket: WebSocket, execution_id: int):
        await websocket.accept()
        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = set()
        self.active_connections[execution_id].add(websocket)

    def disconnect(self, websocket: WebSocket, execution_id: int):
        if execution_id in self.active_connections:
            self.active_connections[execution_id].discard(websocket)
            if not self.active_connections[execution_id]:
                del self.active_connections[execution_id]

    def send_log_sync(self, execution_id: int, log_data: dict):
        """从同步上下文（如线程）调用"""
        if self.loop and execution_id in self.active_connections:
            asyncio.run_coroutine_threadsafe(
                self._send_log_async(execution_id, log_data),
                self.loop
            )

    async def _send_log_async(self, execution_id: int, log_data: dict):
        if execution_id in self.active_connections:
            to_remove = set()
            for connection in self.active_connections[execution_id]:
                try:
                    await connection.send_json(log_data)
                except Exception:
                    to_remove.add(connection)

            # 清理断开的连接
            for conn in to_remove:
                self.active_connections[execution_id].discard(conn)
            if not self.active_connections[execution_id]:
                del self.active_connections[execution_id]
ws_manager = ConnectionManager()
