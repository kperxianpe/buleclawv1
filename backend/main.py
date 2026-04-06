#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blueclaw 后端服务入口
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from websocket.server import BlueclawWebSocketServer
from core.task_manager import task_manager
from core.checkpoint import checkpoint_manager


async def main():
    # 1. 恢复之前的任务
    print("Restoring tasks from checkpoints...")
    await checkpoint_manager.restore_all_tasks(task_manager)
    
    # 2. 启动 WebSocket 服务
    port = int(os.environ.get('PORT', 8000))
    server = BlueclawWebSocketServer(host="localhost", port=port)
    
    # 设置 TaskManager 的服务器引用
    task_manager.set_server(server)
    
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer stopped")
