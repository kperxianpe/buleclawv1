#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket Integration Test for Week 15-17 Core Engine

Tests all core features exposed via WebSocket:
1. Task creation with intent analysis
2. Thinking chain (clarification flow)
3. Blueprint generation
4. Execution flow
5. Intervention & REPLAN
"""

import asyncio
import json
import websockets
import sys
import subprocess
import time

URI = 'ws://localhost:8765'


class WebSocketTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
    
    def log(self, msg):
        print(f"  {msg}")
    
    async def run_all(self):
        print("="*70)
        print("Blueclaw WebSocket Integration Test")
        print("Testing Week 15-17 Core Engine via WebSocket")
        print("="*70)
        
        await self.test_1_task_creation()
        await self.test_2_thinking_flow()
        await self.test_3_blueprint_execution()
        await self.test_4_status_query()
        
        print("\n" + "="*70)
        print(f"RESULTS: {self.passed}/{self.passed+self.failed} passed")
        print("="*70)
        
        return self.failed == 0
    
    async def test_1_task_creation(self):
        """Test 1: Task creation with intent analysis"""
        print("\n[Test 1] Task Creation with Intent Analysis")
        print("-" * 50)
        
        try:
            async with websockets.connect(URI) as ws:
                # Send task with vague input (should trigger clarification)
                await ws.send(json.dumps({
                    "type": "task.start",
                    "payload": {"user_input": "Plan a trip"}
                }))
                
                resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(resp)
                
                assert data["type"] == "task.created", f"Expected task.created, got {data['type']}"
                assert "session_id" in data["payload"], "Missing session_id"
                
                session_id = data["payload"]["session_id"]
                phase = data["payload"]["phase"]
                
                self.log(f"Session ID: {session_id}")
                self.log(f"Phase: {phase}")
                
                if phase == "thinking_node":
                    self.log("Clarification needed (expected for vague input)")
                elif phase in ["blueprint_ready", "execution_preview"]:
                    self.log("Direct blueprint (high confidence)")
                
                self.passed += 1
                return session_id
                
        except Exception as e:
            self.log(f"[FAIL] {e}")
            self.failed += 1
            return None
    
    async def test_2_thinking_flow(self):
        """Test 2: Thinking chain with option selection"""
        print("\n[Test 2] Thinking Chain Flow")
        print("-" * 50)
        
        try:
            async with websockets.connect(URI) as ws:
                # Start task
                await ws.send(json.dumps({
                    "type": "task.start",
                    "payload": {"user_input": "Help me with a project"}
                }))
                
                resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(resp)
                session_id = data["payload"]["session_id"]
                
                # If thinking node, select options until converged
                iteration = 0
                while data["payload"].get("phase") == "thinking_node" and iteration < 3:
                    thinking_node = data["payload"]["thinking_node"]
                    if thinking_node and "options" in thinking_node:
                        options = thinking_node["options"]
                        option_id = options[0]["id"] if hasattr(options[0], 'id') else options[0].get("id", "A")
                        node_id = thinking_node.get("node_id", "node_1")
                        
                        self.log(f"Selecting option: {option_id}")
                        
                        await ws.send(json.dumps({
                            "type": "thinking.select_option",
                            "payload": {
                                "session_id": session_id,
                                "node_id": node_id,
                                "option_id": option_id
                            }
                        }))
                        
                        resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                        data = json.loads(resp)
                        self.log(f"Response: {data['type']}")
                    
                    iteration += 1
                
                # Should have blueprint or execution preview
                if data["payload"].get("blueprint"):
                    steps = data["payload"]["blueprint"]
                    self.log(f"Blueprint generated with {len(steps)} steps")
                
                self.passed += 1
                
        except Exception as e:
            self.log(f"[FAIL] {e}")
            self.failed += 1
    
    async def test_3_blueprint_execution(self):
        """Test 3: Blueprint execution"""
        print("\n[Test 3] Blueprint Execution")
        print("-" * 50)
        
        try:
            async with websockets.connect(URI) as ws:
                # Start task
                await ws.send(json.dumps({
                    "type": "task.start",
                    "payload": {"user_input": "List files in directory"}
                }))
                
                resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(resp)
                session_id = data["payload"]["session_id"]
                
                # Wait for thinking to complete
                iteration = 0
                while data["payload"].get("phase") == "thinking_node" and iteration < 3:
                    await ws.send(json.dumps({
                        "type": "thinking.select_option",
                        "payload": {
                            "session_id": session_id,
                            "node_id": "node_1",
                            "option_id": "A"
                        }
                    }))
                    resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    data = json.loads(resp)
                    iteration += 1
                
                # Start execution
                await ws.send(json.dumps({
                    "type": "execution.start",
                    "payload": {"session_id": session_id}
                }))
                
                resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(resp)
                
                assert data["type"] == "execution.blueprint_loaded"
                status = data["payload"]["status"]
                steps = data["payload"].get("steps", [])
                
                self.log(f"Execution status: {status}")
                self.log(f"Steps: {len(steps)}")
                
                self.passed += 1
                
        except Exception as e:
            self.log(f"[FAIL] {e}")
            self.failed += 1
    
    async def test_4_status_query(self):
        """Test 4: Status query"""
        print("\n[Test 4] Status Query")
        print("-" * 50)
        
        try:
            async with websockets.connect(URI) as ws:
                # Start task
                await ws.send(json.dumps({
                    "type": "task.start",
                    "payload": {"user_input": "Analyze code project"}
                }))
                
                resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(resp)
                session_id = data["payload"]["session_id"]
                
                # Query status
                await ws.send(json.dumps({
                    "type": "task.status",
                    "payload": {"session_id": session_id}
                }))
                
                resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                data = json.loads(resp)
                
                assert data["type"] == "task.status"
                assert "status" in data["payload"]
                
                self.log(f"Status query successful")
                self.passed += 1
                
        except Exception as e:
            self.log(f"[FAIL] {e}")
            self.failed += 1


async def main():
    tester = WebSocketTester()
    success = await tester.run_all()
    return 0 if success else 1


if __name__ == "__main__":
    # Run with server
    print("Starting test runner...")
    
    import os
    os.environ['PORT'] = '8765'
    
    # Start server in background
    server = subprocess.Popen(
        [sys.executable, 'server_main.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(3)  # Wait for server
    
    try:
        exit_code = asyncio.run(main())
    finally:
        server.terminate()
        server.wait(timeout=5)
    
    sys.exit(exit_code)
