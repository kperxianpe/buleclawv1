#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blueclaw WebSocket 服务主入口
"""
import asyncio
import json
import uuid
from typing import Dict, Set
import websockets
from websockets.server import WebSocketServerProtocol


class BlueclawWebSocketServer:
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.host = host
        self.port = port
        # 存储所有连接: {websocket: connection_info}
        self.connections: Dict[WebSocketServerProtocol, dict] = {}
        # 按任务分组: {task_id: Set[websocket]}
        self.task_connections: Dict[str, Set[WebSocketServerProtocol]] = {}
        
    async def start(self):
        """启动 WebSocket 服务"""
        print(f"Starting WebSocket server at ws://{self.host}:{self.port}")
        async with websockets.serve(self._handle_connection, self.host, self.port):
            await asyncio.Future()  # 永远运行
    
    async def _handle_connection(self, websocket: WebSocketServerProtocol):
        """处理新连接"""
        connection_id = str(uuid.uuid4())
        self.connections[websocket] = {
            "id": connection_id,
            "connected_at": asyncio.get_event_loop().time(),
            "task_id": None
        }
        print(f"New connection: {connection_id}")
        
        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            print(f"Connection closed: {connection_id}")
        finally:
            await self._cleanup_connection(websocket)
    
    async def _handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """处理收到的消息"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            # 导入路由器处理消息
            from websocket.message_router import router
            response = await router.route(websocket, data, self)
            
            # 发送响应
            await self.send_to_connection(websocket, response)
            
        except json.JSONDecodeError:
            await self.send_to_connection(websocket, {
                "type": "error",
                "payload": {"message": "Invalid JSON"},
                "timestamp": int(asyncio.get_event_loop().time() * 1000),
                "message_id": str(uuid.uuid4())
            })
    
    async def send_to_connection(self, websocket: WebSocketServerProtocol, message: dict):
        """向单个连接发送消息"""
        try:
            await websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosed:
            pass
    
    async def broadcast_to_task(self, task_id: str, message: dict):
        """向同一任务的所有连接广播消息"""
        if task_id not in self.task_connections:
            return
        
        websockets_set = self.task_connections[task_id].copy()
        for ws in websockets_set:
            await self.send_to_connection(ws, message)
    
    async def _cleanup_connection(self, websocket: WebSocketServerProtocol):
        """清理断开连接的客户端"""
        if websocket in self.connections:
            conn_info = self.connections[websocket]
            task_id = conn_info.get("task_id")
            
            # 从任务分组中移除
            if task_id and task_id in self.task_connections:
                self.task_connections[task_id].discard(websocket)
                if not self.task_connections[task_id]:
                    del self.task_connections[task_id]
            
            del self.connections[websocket]
    
    def associate_connection_with_task(self, websocket: WebSocketServerProtocol, task_id: str):
        """将连接与任务关联"""
        if websocket in self.connections:
            self.connections[websocket]["task_id"] = task_id
        
        if task_id not in self.task_connections:
            self.task_connections[task_id] = set()
        self.task_connections[task_id].add(websocket)
