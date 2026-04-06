#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stress Tests - Load Testing

Tests server behavior under heavy load.
"""

import asyncio
import json
import websockets
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class LoadTest:
    """负载测试"""
    
    def __init__(self, uri='ws://localhost:8765'):
        self.uri = uri
    
    async def test_concurrent_connections(self, num_connections=10):
        """测试并发连接数（降低为10以避免系统限制）"""
        print(f"\n[Load Test] Concurrent connections: {num_connections}")
        
        semaphore = asyncio.Semaphore(5)  # 限制同时连接数
        
        async def create_connection(i):
            async with semaphore:
                try:
                    await asyncio.sleep(0.1)  # 间隔避免瞬间高峰
                    async with websockets.connect(self.uri, timeout=10) as ws:
                        await ws.send(json.dumps({
                            'type': 'task.start',
                            'payload': {'user_input': f'Load test task {i}'}
                        }))
                        resp = await asyncio.wait_for(ws.recv(), timeout=10.0)
                        return json.loads(resp)['payload']['task_id']
                except Exception as e:
                    return f"error: {e}"
        
        start = time.time()
        tasks = [create_connection(i) for i in range(num_connections)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end = time.time()
        
        success = sum(1 for r in results if isinstance(r, str) and r.startswith('task_'))
        errors = num_connections - success
        
        print(f"  Total: {num_connections}")
        print(f"  Success: {success}")
        print(f"  Errors: {errors}")
        print(f"  Time: {end - start:.2f}s")
        print(f"  Throughput: {success / (end - start):.1f} tasks/sec")
    
    async def test_message_rate(self, messages_per_second=100, duration=10):
        """测试消息速率"""
        print(f"\n[Load Test] Message rate: {messages_per_second}/sec for {duration}s")
        
        async with websockets.connect(self.uri) as ws:
            sent = 0
            received = 0
            errors = 0
            
            start = time.time()
            
            async def sender():
                nonlocal sent
                interval = 1.0 / messages_per_second
                while time.time() - start < duration:
                    try:
                        await ws.send(json.dumps({
                            'type': 'task.start',
                            'payload': {'user_input': f'Msg {sent}'}
                        }))
                        sent += 1
                        await asyncio.sleep(interval)
                    except Exception as e:
                        print(f"Send error: {e}")
                        break
            
            async def receiver():
                nonlocal received, errors
                while time.time() - start < duration + 5:  # Extra time to drain
                    try:
                        resp = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        received += 1
                    except asyncio.TimeoutError:
                        if time.time() - start > duration:
                            break
                    except Exception as e:
                        errors += 1
            
            await asyncio.gather(sender(), receiver())
            
            print(f"  Sent: {sent}")
            print(f"  Received: {received}")
            print(f"  Errors: {errors}")
            print(f"  Loss rate: {(sent - received) / sent * 100:.1f}%")
    
    async def test_memory_leak(self, iterations=100):
        """测试内存泄漏（通过观察响应时间）"""
        print(f"\n[Load Test] Memory leak check: {iterations} iterations")
        
        response_times = []
        
        for i in range(iterations):
            start = time.time()
            try:
                async with websockets.connect(self.uri) as ws:
                    await ws.send(json.dumps({
                        'type': 'task.start',
                        'payload': {'user_input': f'Test {i}'}
                    }))
                    await asyncio.wait_for(ws.recv(), timeout=10.0)
            except Exception as e:
                print(f"Iteration {i} failed: {e}")
            
            elapsed = time.time() - start
            response_times.append(elapsed)
            
            # 每20次报告一次
            if (i + 1) % 20 == 0:
                avg = sum(response_times[-20:]) / 20
                print(f"  Iterations {i-18}-{i+1}: avg {avg:.2f}s")
    
    async def run_all(self):
        """运行所有压力测试"""
        print("="*70)
        print("Stress Tests - Load Testing")
        print("="*70)
        
        await self.test_concurrent_connections(20)
        await self.test_message_rate(50, 5)
        # await self.test_memory_leak(100)  # 耗时较长，默认不运行
        
        print("\n" + "="*70)
        print("Load tests completed")
        print("="*70)


async def main():
    test = LoadTest()
    await test.run_all()


if __name__ == "__main__":
    asyncio.run(main())
