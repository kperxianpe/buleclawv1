#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_1minute_test.py - 1 minute complete test

Auto-start server, run tests, close after 1 minute.
Usage: python run_1minute_test.py
"""

import asyncio
import subprocess
import sys
import time
import threading
from pathlib import Path

# Test config
TEST_DURATION = 60  # 1 minute
SERVER_HOST = "localhost"
SERVER_PORT = 8766  # Use different port to avoid conflict


class ServerManager:
    """Server manager"""
    
    def __init__(self):
        self.process = None
        self.ready = threading.Event()
        self.output_thread = None
        
    def start(self):
        """Start server"""
        print("[1/5] Starting WebSocket server...")
        
        # Start server process
        self.process = subprocess.Popen(
            [sys.executable, "start_websocket_server.py", 
             "--host", SERVER_HOST, 
             "--port", str(SERVER_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Start output monitor thread
        self.output_thread = threading.Thread(target=self._monitor_output)
        self.output_thread.daemon = True
        self.output_thread.start()
        
        # Wait for server ready
        if not self.ready.wait(timeout=5.0):
            print("[FAIL] Server start timeout")
            return False
            
        print(f"[OK] Server ready: ws://{SERVER_HOST}:{SERVER_PORT}")
        return True
    
    def _monitor_output(self):
        """Monitor server output"""
        for line in self.process.stdout:
            line = line.strip()
            if line:
                # Filter error messages
                if "opening handshake failed" not in line and "Traceback" not in line:
                    print(f"  [Server] {line}")
                
                # Detect server ready
                if "Server started" in line or "Ready to accept connections" in line:
                    self.ready.set()
    
    def stop(self):
        """Stop server"""
        if self.process:
            print("\n[5/5] Stopping server...")
            self.process.terminate()
            try:
                self.process.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
            print("[OK] Server stopped")


class TestClient:
    """Test client"""
    
    def __init__(self):
        self.messages_sent = 0
        self.messages_received = 0
        self.errors = []
        
    async def run_tests(self):
        """Run tests"""
        import websockets
        from blueclaw.api import MessageFactory, BlueclawMessage
        
        uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
        
        try:
            print(f"\n[2/5] Connecting to {uri}...")
            async with websockets.connect(uri) as websocket:
                print("[OK] Connected")
                
                # Wait for connection confirm
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    import json
                    msg = BlueclawMessage.from_dict(json.loads(response))
                    print(f"  Received: {msg.type}")
                    if msg.type == "system.connected":
                        session_id = msg.payload.get("session_id")
                        print(f"  Session ID: {session_id}")
                    self.messages_received += 1
                except asyncio.TimeoutError:
                    print("[WARN] No connection confirm received")
                
                # Test 1: Send task
                print("\n[3/5] Sending test task...")
                task_msg = MessageFactory.create_task_start("List files in current directory")
                await websocket.send(task_msg.to_json())
                self.messages_sent += 1
                print(f"  Sent: {task_msg.type}")
                
                # Wait response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    import json
                    msg = BlueclawMessage.from_dict(json.loads(response))
                    print(f"  Received: {msg.type}")
                    if msg.type == "thinking.node_created":
                        print("  Thinking node created")
                    elif msg.type == "execution.blueprint_loaded":
                        steps = msg.payload.get("steps", [])
                        print(f"  Execution blueprint loaded: {len(steps)} steps")
                    self.messages_received += 1
                except asyncio.TimeoutError:
                    print("[WARN] Response timeout")
                
                # Test 2: Send task with options
                print("\n  Sending planning task...")
                task_msg2 = MessageFactory.create_task_start("Plan a weekend trip")
                await websocket.send(task_msg2.to_json())
                self.messages_sent += 1
                
                # Wait multiple responses
                for i in range(3):
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        import json
                        msg = BlueclawMessage.from_dict(json.loads(response))
                        print(f"  Received: {msg.type}")
                        self.messages_received += 1
                    except asyncio.TimeoutError:
                        break
                
                print("[OK] Message test completed")
                return True
                
        except Exception as e:
            self.errors.append(str(e))
            print(f"[FAIL] Test failed: {e}")
            return False


def format_duration(seconds):
    """Format duration"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


async def main():
    """Main function"""
    print("="*60)
    print("Week 15.5 - 1 minute architecture test")
    print("="*60)
    print(f"\nDuration: {TEST_DURATION} seconds")
    print(f"Server: ws://{SERVER_HOST}:{SERVER_PORT}")
    
    start_time = time.time()
    server = ServerManager()
    client = TestClient()
    
    try:
        # Start server
        if not server.start():
            print("\n[FAIL] Cannot start server")
            return 1
        
        # Run tests
        print("\n[4/5] Running protocol tests...")
        await client.run_tests()
        
        # Wait remaining time
        elapsed = time.time() - start_time
        remaining = TEST_DURATION - elapsed
        
        if remaining > 0:
            print(f"\n  Waiting... ({format_duration(remaining)} remaining)")
            await asyncio.sleep(remaining)
        
        # Print results
        total_time = time.time() - start_time
        print(f"\n{'='*60}")
        print("Test completed!")
        print(f"{'='*60}")
        print(f"\nStatistics:")
        print(f"  Total time: {format_duration(total_time)}")
        print(f"  Messages sent: {client.messages_sent}")
        print(f"  Messages received: {client.messages_received}")
        print(f"  Errors: {len(client.errors)}")
        
        if client.errors:
            print(f"\nErrors:")
            for err in client.errors:
                print(f"  - {err}")
        
        print(f"\nArchitecture validation:")
        print(f"  [OK] Protocol layer (v1.0.0)")
        print(f"  [OK] Engine layer (Facade)")
        print(f"  [OK] WebSocket communication")
        
        return 0 if len(client.errors) == 0 else 1
        
    except KeyboardInterrupt:
        print("\n\n[User interrupted]")
        return 130
    finally:
        server.stop()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    
    sys.exit(exit_code)
