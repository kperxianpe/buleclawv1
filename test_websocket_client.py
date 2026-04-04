#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_websocket_client.py - WebSocket 测试客户端

简单的命令行客户端，用于测试 WebSocket 服务器和消息协议。
不需要 npm，只需要 Python 和 websockets。

用法:
    python test_websocket_client.py
    python test_websocket_client.py --host localhost --port 8765
"""

import asyncio
import argparse
import json
import sys
from datetime import datetime

import websockets

from blueclaw.api import MessageFactory, MessageType, BlueclawMessage


class WebSocketTestClient:
    """WebSocket 测试客户端"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.uri = f"ws://{host}:{port}"
        self.websocket = None
        self.connected = False
        self.session_id = None
        
    async def connect(self):
        """连接到服务器"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.connected = True
            print(f"[OK] Connected to {self.uri}")
            
            # 启动消息接收循环
            asyncio.create_task(self.receive_loop())
            return True
        except Exception as e:
            print(f"[FAIL] Connection failed: {e}")
            return False
    
    async def receive_loop(self):
        """接收消息的循环"""
        try:
            async for message in self.websocket:
                await self.handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            print("[INFO] Connection closed")
            self.connected = False
    
    async def handle_message(self, raw_message: str):
        """Handle received message"""
        try:
            data = json.loads(raw_message)
            msg = BlueclawMessage.from_dict(data)
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] << {msg.type}")
            
            if msg.type == MessageType.CONNECTED:
                self.session_id = msg.payload.get("session_id")
                print(f"  Session ID: {self.session_id}")
                print(f"  Protocol Version: {msg.payload.get('protocol_version')}")
                
            elif msg.type == MessageType.THINKING_NODE_CREATED:
                node = msg.payload
                print(f"  Question: {node.get('question', 'N/A')}")
                options = node.get('options', [])
                if options:
                    print(f"  Options:")
                    for opt in options:
                        default_mark = " (default)" if opt.get('is_default') else ""
                        print(f"    [{opt['id']}] {opt['label']}{default_mark}")
                        
            elif msg.type == MessageType.EXECUTION_BLUEPRINT_LOADED:
                steps = msg.payload.get('steps', [])
                print(f"  Loaded {len(steps)} execution steps:")
                for i, step in enumerate(steps):
                    print(f"    {i+1}. {step.get('name')}")
                    
            elif msg.type == MessageType.EXECUTION_STEP_STARTED:
                print(f"  Step: {msg.payload.get('step_name')}")
                print(f"  Index: {msg.payload.get('index')}")
                
            elif msg.type == MessageType.EXECUTION_STEP_COMPLETED:
                print(f"  Step ID: {msg.payload.get('step_id')}")
                print(f"  Duration: {msg.payload.get('duration_ms', 0):.0f}ms")
                
            elif msg.type == MessageType.EXECUTION_COMPLETED:
                success = msg.payload.get('success')
                summary = msg.payload.get('summary')
                status = "SUCCESS" if success else "FAILED"
                print(f"  Status: {status}")
                print(f"  Summary: {summary}")
                
            elif msg.type == MessageType.ERROR:
                print(f"  Error Code: {msg.payload.get('error_code')}")
                print(f"  Message: {msg.payload.get('error_message')}")
                
            else:
                # 其他消息类型，打印 payload
                print(f"  Payload: {json.dumps(msg.payload, ensure_ascii=False, indent=2)[:200]}...")
                
        except Exception as e:
            print(f"[ERROR] Failed to handle message: {e}")
    
    async def send_message(self, msg: BlueclawMessage):
        """发送消息"""
        if not self.connected or not self.websocket:
            print("[FAIL] Not connected")
            return
            
        await self.websocket.send(msg.to_json())
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] >> {msg.type}")
    
    async def start_task(self, user_input: str):
        """开始任务"""
        msg = MessageFactory.create_task_start(user_input)
        await self.send_message(msg)
    
    async def select_option(self, node_id: str, option_id: str):
        """选择选项"""
        msg = MessageFactory.create_select_option(node_id, option_id)
        await self.send_message(msg)
    
    async def intervene(self, step_id: str, action_type: str):
        """干预"""
        msg = MessageFactory.create_intervene(step_id, action_type)
        await self.send_message(msg)
    
    async def disconnect(self):
        """断开连接"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False


async def interactive_client(host: str, port: int):
    """交互式客户端"""
    client = WebSocketTestClient(host, port)
    
    if not await client.connect():
        return
    
    # 等待连接确认
    await asyncio.sleep(0.5)
    
    print("\n" + "="*60)
    print("Blueclaw WebSocket Test Client")
    print("Commands:")
    print("  task <input>     - Start a task")
    print("  select <nid> <oid> - Select an option")
    print("  intervene <sid> <action> - Intervene (replan/skip/stop)")
    print("  quit             - Exit")
    print("="*60 + "\n")
    
    while client.connected:
        try:
            # 获取用户输入
            user_input = await asyncio.get_event_loop().run_in_executor(
                None, lambda: input("\n> ")
            )
            
            if not user_input.strip():
                continue
                
            parts = user_input.strip().split()
            command = parts[0].lower()
            
            if command == "quit" or command == "exit":
                break
                
            elif command == "task":
                if len(parts) < 2:
                    print("Usage: task <input>")
                    continue
                task_input = " ".join(parts[1:])
                await client.start_task(task_input)
                
            elif command == "select":
                if len(parts) < 3:
                    print("Usage: select <node_id> <option_id>")
                    continue
                await client.select_option(parts[1], parts[2])
                
            elif command == "intervene":
                if len(parts) < 3:
                    print("Usage: intervene <step_id> <action>")
                    print("Actions: replan, skip, stop, retry")
                    continue
                await client.intervene(parts[1], parts[2])
                
            else:
                print(f"Unknown command: {command}")
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[ERROR] {e}")
    
    await client.disconnect()
    print("\n[OK] Client disconnected")


async def run_tests(host: str, port: int):
    """运行自动化测试"""
    client = WebSocketTestClient(host, port)
    
    print("\n" + "="*60)
    print("Running WebSocket Protocol Tests")
    print("="*60)
    
    # 测试 1: 连接
    print("\n[Test 1] Connect to server...")
    if not await client.connect():
        print("[FAIL] Connection test failed")
        return False
    await asyncio.sleep(0.5)
    
    # 测试 2: 发送任务
    print("\n[Test 2] Start a task...")
    await client.start_task("列出当前目录的文件")
    await asyncio.sleep(2)
    
    # 测试 3: 发送带选项的任务
    print("\n[Test 3] Start a task with options...")
    await client.start_task("规划一个周末旅行")
    await asyncio.sleep(2)
    
    # 断开连接
    await client.disconnect()
    
    print("\n" + "="*60)
    print("Tests completed")
    print("="*60)
    return True


def main():
    parser = argparse.ArgumentParser(description='Blueclaw WebSocket Test Client')
    parser.add_argument('--host', default='localhost', help='Server host (default: localhost)')
    parser.add_argument('--port', type=int, default=8765, help='Server port (default: 8765)')
    parser.add_argument('--test', action='store_true', help='Run automated tests')
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(run_tests(args.host, args.port))
    else:
        asyncio.run(interactive_client(args.host, args.port))


if __name__ == "__main__":
    main()
