#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Stable Tests - Week 18.5

Basic functionality tests without heavy load.
"""

import asyncio
import json
import websockets
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

URI = 'ws://localhost:8765'


async def test_basic_flow():
    """测试基本流程"""
    print("="*60)
    print("Simple Functionality Test")
    print("="*60)
    
    passed = 0
    failed = 0
    
    # Test 1: Create task
    print("\n[Test 1] Create task...")
    try:
        async with websockets.connect(URI, open_timeout=10, close_timeout=10) as ws:
            await ws.send(json.dumps({
                'type': 'task.start',
                'payload': {'user_input': 'Test task'}
            }))
            resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(resp)
            assert data['type'] == 'task.created', f"Expected task.created, got {data['type']}"
            task_id = data['payload']['task_id']
            print(f"  [PASS] Task created: {task_id}")
            passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1
    
    # Test 2: Select option
    print("\n[Test 2] Select option...")
    try:
        async with websockets.connect(URI, timeout=10) as ws:
            # Create task first
            await ws.send(json.dumps({
                'type': 'task.start',
                'payload': {'user_input': 'Task with option'}
            }))
            resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(resp)
            task_id = data['payload']['task_id']
            
            # Select option
            await ws.send(json.dumps({
                'type': 'thinking.select_option',
                'payload': {'task_id': task_id, 'node_id': 'n1', 'option_id': 'A'}
            }))
            resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(resp)
            assert data['type'] == 'thinking.node_selected'
            print(f"  [PASS] Option selected")
            passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1
    
    # Test 3: Cancel task
    print("\n[Test 3] Cancel task...")
    try:
        async with websockets.connect(URI, timeout=10) as ws:
            # Create
            await ws.send(json.dumps({
                'type': 'task.start',
                'payload': {'user_input': 'Task to cancel'}
            }))
            resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
            task_id = json.loads(resp)['payload']['task_id']
            
            # Cancel
            await ws.send(json.dumps({
                'type': 'task.cancel',
                'payload': {'task_id': task_id}
            }))
            resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(resp)
            assert data['type'] == 'task.cancelled'
            print(f"  [PASS] Task cancelled")
            passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1
    
    # Test 4: Error handling
    print("\n[Test 4] Error handling...")
    try:
        async with websockets.connect(URI, timeout=10) as ws:
            await ws.send(json.dumps({
                'type': 'unknown.type',
                'payload': {}
            }))
            resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
            data = json.loads(resp)
            assert data['type'] == 'error'
            print(f"  [PASS] Error returned correctly")
            passed += 1
    except Exception as e:
        print(f"  [FAIL] {e}")
        failed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"Results: {passed}/{passed+failed} passed")
    print("="*60)
    
    return failed == 0


async def main():
    success = await test_basic_flow()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
