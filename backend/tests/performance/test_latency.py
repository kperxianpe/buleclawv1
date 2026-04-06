#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance Tests - Latency Measurement

Measures response times for various operations.
"""

import asyncio
import json
import websockets
import sys
import os
import time
import statistics

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class LatencyTest:
    """延迟测试"""
    
    def __init__(self, uri='ws://localhost:8765'):
        self.uri = uri
        self.results = {}
    
    async def measure_latency(self, name, operation, iterations=10):
        """测量操作延迟"""
        latencies = []
        
        for _ in range(iterations):
            start = time.time()
            await operation()
            end = time.time()
            latencies.append((end - start) * 1000)  # ms
        
        self.results[name] = {
            'min': min(latencies),
            'max': max(latencies),
            'avg': statistics.mean(latencies),
            'median': statistics.median(latencies),
            'p95': sorted(latencies)[int(iterations * 0.95)],
            'p99': sorted(latencies)[int(iterations * 0.99)] if iterations >= 100 else None
        }
    
    async def run_all(self):
        """运行所有延迟测试"""
        print("="*70)
        print("Performance Test - Latency Measurement")
        print("="*70)
        
        # 1. 连接建立延迟
        async def connect_latency():
            async with websockets.connect(self.uri) as ws:
                pass
        
        await self.measure_latency('Connection Establishment', connect_latency, 10)
        
        # 2. 任务创建延迟
        async def create_task_latency():
            async with websockets.connect(self.uri) as ws:
                await ws.send(json.dumps({
                    'type': 'task.start',
                    'payload': {'user_input': 'Test task'}
                }))
                await asyncio.wait_for(ws.recv(), timeout=10.0)
        
        await self.measure_latency('Task Creation', create_task_latency, 10)
        
        # 3. 简单消息往返延迟
        async def echo_latency():
            async with websockets.connect(self.uri) as ws:
                await ws.send(json.dumps({
                    'type': 'echo',
                    'payload': {'test': 'data'}
                }))
                await asyncio.wait_for(ws.recv(), timeout=10.0)
        
        await self.measure_latency('Simple Message Round-trip', echo_latency, 20)
        
        # 打印结果
        self.print_results()
    
    def print_results(self):
        """打印结果"""
        print("\n" + "="*70)
        print("LATENCY RESULTS (milliseconds)")
        print("="*70)
        print(f"{'Operation':<30} {'Min':>8} {'Avg':>8} {'P95':>8} {'Max':>8}")
        print("-"*70)
        
        for name, metrics in self.results.items():
            print(f"{name:<30} {metrics['min']:>8.1f} {metrics['avg']:>8.1f} "
                  f"{metrics['p95']:>8.1f} {metrics['max']:>8.1f}")
        
        print("="*70)


async def main():
    test = LatencyTest()
    await test.run_all()


if __name__ == "__main__":
    asyncio.run(main())
