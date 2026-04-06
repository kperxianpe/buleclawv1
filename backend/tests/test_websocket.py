#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket 集成测试
"""
import asyncio
import websockets
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_full_flow():
    """测试完整流程"""
    uri = 'ws://localhost:8765'
    
    print("=" * 60)
    print("WebSocket Integration Test")
    print("=" * 60)
    
    try:
        async with websockets.connect(uri) as ws:
            # Test 1: 任务创建
            print("\n[TEST 1] Create task")
            await ws.send(json.dumps({
                'type': 'task.start',
                'payload': {'user_input': '帮我规划周末旅行'}
            }))
            
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(response)
            assert data['type'] == 'task.created', f"Expected task.created, got {data['type']}"
            task_id = data['payload']['task_id']
            print(f"[PASS] Task created: {task_id}")
            
            # Test 2: 选项选择
            print("\n[TEST 2] Select option")
            await ws.send(json.dumps({
                'type': 'thinking.select_option',
                'payload': {'task_id': task_id, 'node_id': 'node_1', 'option_id': 'A'}
            }))
            
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"[PASS] Response type: {data['type']}")
            
            # Test 3: 执行开始
            print("\n[TEST 3] Start execution")
            await ws.send(json.dumps({
                'type': 'execution.start',
                'payload': {'task_id': task_id}
            }))
            
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"[PASS] Response type: {data['type']}")
            
            print("\n" + "=" * 60)
            print("All tests passed!")
            print("=" * 60)
            return True
            
    except (ConnectionRefusedError, OSError):
        print("[FAIL] Connection refused - is server running?")
        return False
    except Exception as e:
        print(f"[FAIL] Test error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_connections():
    """测试多连接 - 串行方式"""
    uri = 'ws://localhost:8765'
    
    print("\n[TEST 4] Multiple connections")
    
    try:
        # 第一个连接
        async with websockets.connect(uri) as ws1:
            await ws1.send(json.dumps({
                'type': 'task.start',
                'payload': {'user_input': 'Task 1'}
            }))
            resp1 = await asyncio.wait_for(ws1.recv(), timeout=5.0)
            task1 = json.loads(resp1)['payload']['task_id']
        
        # 第二个连接（第一个已关闭）
        async with websockets.connect(uri) as ws2:
            await ws2.send(json.dumps({
                'type': 'task.start',
                'payload': {'user_input': 'Task 2'}
            }))
            resp2 = await asyncio.wait_for(ws2.recv(), timeout=5.0)
            task2 = json.loads(resp2)['payload']['task_id']
        
        assert task1 != task2, "Task IDs should be different"
        print(f"[PASS] Two tasks: {task1}, {task2}")
        return True
    except Exception as e:
        print(f"[FAIL] {e}")
        return False


async def main():
    results = []
    results.append(await test_full_flow())
    results.append(await test_multiple_connections())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} test suites passed")
    print("=" * 60)
    
    return all(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
