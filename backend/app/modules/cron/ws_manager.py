import asyncio
from datetime import datetime
from fastapi import WebSocket
from typing import Dict, Set, Deque
from collections import deque

from app.modules.cron.execution_manager import execution_manager

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.log_cache: Dict[int, list] = {}
        self.message_queues: Dict[int, Deque[dict]] = {}
        self.queue_workers: Dict[int, asyncio.Task] = {}
        self.loop = None

    def set_event_loop(self, loop):
        self.loop = loop

    async def connect(self, websocket: WebSocket, execution_id: int):
        await websocket.accept()
        if execution_id not in self.active_connections:
            self.active_connections[execution_id] = set()
            self.message_queues[execution_id] = deque()

        self.active_connections[execution_id].add(websocket)

        if execution_id not in self.queue_workers or self.queue_workers[execution_id].done():
            self.queue_workers[execution_id] = asyncio.create_task(
                self._process_message_queue(execution_id)
            )

        if execution_id in self.log_cache:
            for log_data in self.log_cache[execution_id]:
                self.message_queues[execution_id].append(log_data.copy())

    async def _process_message_queue(self, execution_id: int):
        while True:
            # 🔑 关键1：每次循环强制释放控制权
            await asyncio.sleep(0)

            # 🔑 关键2：循环开始立即检查中断
            if execution_manager.should_stop(execution_id):
                # print(f'ws {datetime.now()} - 收到停止信号，立即退出')
                break

            try:
                # 检查队列
                if not self.message_queues[execution_id]:
                    await asyncio.sleep(0.05)
                    continue

                # 🔑 关键3：处理消息前再次检查
                if execution_manager.should_stop(execution_id):
                    # print(f'ws {datetime.now()} - 处理中收到停止信号')
                    break

                # 处理单条消息
                log_data = self.message_queues[execution_id].popleft()

                # 🔑 关键4：仅当有连接时才广播
                if execution_id in self.active_connections and self.active_connections[execution_id]:
                    to_remove = set()
                    for connection in self.active_connections[execution_id]:
                        try:
                            await connection.send_json(log_data)
                        except Exception:
                            to_remove.add(connection)

                    # 清理失效连接
                    for conn in to_remove:
                        self.active_connections[execution_id].discard(conn)

                # 🔑 关键5：无连接时主动休眠（防止CPU 100%）
                elif len(self.message_queues[execution_id]) > 100:
                    await asyncio.sleep(0.01)

            except Exception as e:
                print(f"处理消息队列失败: {e}")
                break

        # 清理资源
        self._cleanup_execution(execution_id)

    def _cleanup_execution(self, execution_id: int):
        """统一清理资源"""
        if execution_id in self.active_connections:
            del self.active_connections[execution_id]
        if execution_id in self.message_queues:
            del self.message_queues[execution_id]
        if execution_id in self.queue_workers:
            self.queue_workers[execution_id].cancel()

    def disconnect(self, websocket: WebSocket, execution_id: int):
        if execution_id in self.active_connections:
            self.active_connections[execution_id].discard(websocket)
            if not self.active_connections[execution_id]:
                del self.active_connections[execution_id]

    def send_log_sync(self, execution_id: int, log_data: dict):
        #先放入缓存
        if execution_id not in self.log_cache:
            self.log_cache[execution_id] = []
        self.log_cache[execution_id].append(log_data)

        #消息队列
        if execution_id not in self.message_queues:
            return

        # 限制队列长度防内存爆炸
        if len(self.message_queues[execution_id]) > 10000:
            return

        # 通过事件循环线程安全入队
        if self.loop:
            self.loop.call_soon_threadsafe(
                self.message_queues[execution_id].append,
                log_data.copy()
            )

    def cleanup(self, execution_id: int):
        self._cleanup_execution(execution_id)
        if execution_id in self.log_cache:
            del self.log_cache[execution_id]

ws_manager = ConnectionManager()
