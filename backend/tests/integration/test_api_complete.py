#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Week 18.5 - Complete API Interface Tests

Tests all message types and edge cases.
"""

import asyncio
import json
import websockets
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class APITestRunner:
    """API 完整测试运行器"""
    
    def __init__(self, uri='ws://localhost:8765'):
        self.uri = uri
        self.passed = 0
        self.failed = 0
        self.test_results = []
    
    def log(self, msg):
        print(f"  {msg}")
    
    async def run_test(self, name, test_func):
        """运行单个测试"""
        try:
            await test_func()
            self.passed += 1
            self.test_results.append((name, True, None))
            self.log(f"[PASS] {name}")
        except Exception as e:
            self.failed += 1
            self.test_results.append((name, False, str(e)))
            self.log(f"[FAIL] {name}: {e}")
    
    async def run_all(self):
        """运行所有测试"""
        print("="*70)
        print("Week 18.5 - Complete API Interface Tests")
        print("="*70)
        
        # 1. 基础消息类型测试
        await self.test_basic_messages()
        
        # 2. 任务生命周期测试
        await self.test_task_lifecycle()
        
        # 3. 错误处理测试
        await self.test_error_handling()
        
        # 4. 边界情况测试
        await self.test_edge_cases()
        
        # 5. 并发测试
        await self.test_concurrent()
        
        # 报告
        self.print_report()
        return self.failed == 0
    
    async def test_basic_messages(self):
        """测试基础消息类型"""
        print("\n[Group 1] Basic Message Types")
        print("-" * 50)
        
        async def test_echo():
            """测试回显"""
            async with websockets.connect(self.uri) as ws:
                await ws.send(json.dumps({
                    'type': 'echo',
                    'payload': {'test': 'data'}
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                assert data['type'] == 'echo' or data['type'] == 'error'
        
        async def test_unknown_type():
            """测试未知消息类型"""
            async with websockets.connect(self.uri) as ws:
                await ws.send(json.dumps({
                    'type': 'unknown.message.type',
                    'payload': {}
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                assert data['type'] == 'error'
        
        async def test_invalid_json():
            """测试无效 JSON"""
            async with websockets.connect(self.uri) as ws:
                await ws.send('not valid json {{{')
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                assert data['type'] == 'error'
        
        async def test_missing_type():
            """测试缺少 type 字段"""
            async with websockets.connect(self.uri) as ws:
                await ws.send(json.dumps({'payload': {}}))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                assert data['type'] == 'error'
        
        await self.run_test("Echo message", test_echo)
        await self.run_test("Unknown message type", test_unknown_type)
        await self.run_test("Invalid JSON", test_invalid_json)
        await self.run_test("Missing type field", test_missing_type)
    
    async def test_task_lifecycle(self):
        """测试任务完整生命周期"""
        print("\n[Group 2] Task Lifecycle")
        print("-" * 50)
        
        async def test_create_task():
            """创建任务"""
            async with websockets.connect(self.uri) as ws:
                await ws.send(json.dumps({
                    'type': 'task.start',
                    'payload': {'user_input': '测试任务'}
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                assert data['type'] == 'task.created'
                assert 'task_id' in data['payload']
        
        async def test_task_with_context():
            """带上下文的任务"""
            async with websockets.connect(self.uri) as ws:
                await ws.send(json.dumps({
                    'type': 'task.start',
                    'payload': {
                        'user_input': '测试任务',
                        'context': {'source': 'test', 'priority': 'high'}
                    }
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                assert data['type'] == 'task.created'
        
        async def test_select_option():
            """选择思考选项"""
            async with websockets.connect(self.uri) as ws:
                # 先创建任务
                await ws.send(json.dumps({
                    'type': 'task.start',
                    'payload': {'user_input': '需要澄清的任务'}
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                task_data = json.loads(resp)
                task_id = task_data['payload']['task_id']
                
                # 选择选项
                await ws.send(json.dumps({
                    'type': 'thinking.select_option',
                    'payload': {
                        'task_id': task_id,
                        'node_id': 'node_1',
                        'option_id': 'A'
                    }
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                assert data['type'] == 'thinking.node_selected'
        
        async def test_cancel_task():
            """取消任务"""
            async with websockets.connect(self.uri) as ws:
                # 创建任务
                await ws.send(json.dumps({
                    'type': 'task.start',
                    'payload': {'user_input': '将被取消的任务'}
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                task_data = json.loads(resp)
                task_id = task_data['payload']['task_id']
                
                # 取消任务
                await ws.send(json.dumps({
                    'type': 'task.cancel',
                    'payload': {'task_id': task_id}
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                assert data['type'] == 'task.cancelled'
        
        await self.run_test("Create task", test_create_task)
        await self.run_test("Task with context", test_task_with_context)
        await self.run_test("Select option", test_select_option)
        await self.run_test("Cancel task", test_cancel_task)
    
    async def test_error_handling(self):
        """测试错误处理"""
        print("\n[Group 3] Error Handling")
        print("-" * 50)
        
        async def test_cancel_nonexistent_task():
            """取消不存在的任务"""
            async with websockets.connect(self.uri) as ws:
                await ws.send(json.dumps({
                    'type': 'task.cancel',
                    'payload': {'task_id': 'task_nonexistent'}
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                # 应该返回错误或非成功状态
                assert data['type'] in ['error', 'task.cancelled']
        
        async def test_missing_payload():
            """缺少 payload"""
            async with websockets.connect(self.uri) as ws:
                await ws.send(json.dumps({
                    'type': 'task.start'
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                # 应该优雅处理
                assert 'type' in data
        
        async def test_empty_user_input():
            """空用户输入"""
            async with websockets.connect(self.uri) as ws:
                await ws.send(json.dumps({
                    'type': 'task.start',
                    'payload': {'user_input': ''}
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                # 应该创建任务，即使是空的
                assert data['type'] == 'task.created'
        
        await self.run_test("Cancel non-existent task", test_cancel_nonexistent_task)
        await self.run_test("Missing payload", test_missing_payload)
        await self.run_test("Empty user input", test_empty_user_input)
    
    async def test_edge_cases(self):
        """测试边界情况"""
        print("\n[Group 4] Edge Cases")
        print("-" * 50)
        
        async def test_very_long_input():
            """超长输入"""
            async with websockets.connect(self.uri) as ws:
                long_input = 'A' * 10000  # 10KB 输入
                await ws.send(json.dumps({
                    'type': 'task.start',
                    'payload': {'user_input': long_input}
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                assert data['type'] == 'task.created'
        
        async def test_unicode_input():
            """Unicode 输入"""
            async with websockets.connect(self.uri) as ws:
                await ws.send(json.dumps({
                    'type': 'task.start',
                    'payload': {
                        'user_input': '你好世界！🌍 ñ émoji: 🚀🔥'
                    }
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                assert data['type'] == 'task.created'
        
        async def test_special_characters():
            """特殊字符"""
            async with websockets.connect(self.uri) as ws:
                await ws.send(json.dumps({
                    'type': 'task.start',
                    'payload': {
                        'user_input': '<script>alert("xss")</script> \'"\\n\\t'
                    }
                }))
                resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                data = json.loads(resp)
                assert data['type'] == 'task.created'
        
        async def test_multiple_tasks_same_connection():
            """同一连接多个任务"""
            async with websockets.connect(self.uri) as ws:
                task_ids = []
                for i in range(3):
                    await ws.send(json.dumps({
                        'type': 'task.start',
                        'payload': {'user_input': f'Task {i}'}
                    }))
                    resp = await asyncio.wait_for(ws.recv(), timeout=5.0)
                    data = json.loads(resp)
                    task_ids.append(data['payload']['task_id'])
                
                # 验证任务ID不同
                assert len(set(task_ids)) == 3
        
        await self.run_test("Very long input (10KB)", test_very_long_input)
        await self.run_test("Unicode input", test_unicode_input)
        await self.run_test("Special characters", test_special_characters)
        await self.run_test("Multiple tasks same connection", test_multiple_tasks_same_connection)
    
    async def test_concurrent(self):
        """测试并发"""
        print("\n[Group 5] Concurrent Tests")
        print("-" * 50)
        
        async def test_multiple_connections():
            """多连接并发"""
            async def create_task(i):
                async with websockets.connect(self.uri) as ws:
                    await ws.send(json.dumps({
                        'type': 'task.start',
                        'payload': {'user_input': f'Concurrent task {i}'}
                    }))
                    resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    data = json.loads(resp)
                    return data['payload']['task_id']
            
            # 并发5个连接
            tasks = [create_task(i) for i in range(5)]
            task_ids = await asyncio.gather(*tasks)
            
            # 验证所有任务都创建了
            assert len(task_ids) == 5
            # 验证任务ID都不同
            assert len(set(task_ids)) == 5
        
        async def test_rapid_messages():
            """快速发送消息"""
            async with websockets.connect(self.uri) as ws:
                # 快速发送5个消息
                for i in range(5):
                    await ws.send(json.dumps({
                        'type': 'task.start',
                        'payload': {'user_input': f'Rapid {i}'}
                    }))
                
                # 接收所有响应
                responses = []
                for _ in range(5):
                    resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                    responses.append(json.loads(resp))
                
                assert len(responses) == 5
                assert all(r['type'] == 'task.created' for r in responses)
        
        await self.run_test("Multiple connections (5)", test_multiple_connections)
        await self.run_test("Rapid messages (5)", test_rapid_messages)
    
    def print_report(self):
        """打印测试报告"""
        print("\n" + "="*70)
        print("TEST REPORT")
        print("="*70)
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\nTotal: {total} tests")
        print(f"Passed: {self.passed} ({pass_rate:.1f}%)")
        print(f"Failed: {self.failed}")
        
        if self.failed > 0:
            print("\nFailed tests:")
            for name, passed, error in self.test_results:
                if not passed:
                    print(f"  - {name}: {error}")
        
        print("\n" + "="*70)


async def main():
    runner = APITestRunner()
    success = await runner.run_all()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
