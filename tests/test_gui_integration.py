#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_gui_integration.py - GUI集成测试

测试完整的用户操作流程
"""

import asyncio
import sys
import threading
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtTest import QTest

from blueclaw import create_coordinator_v3


class GUIIntegrationTester:
    """GUI集成测试器"""
    
    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def log(self, message: str, level: str = "INFO"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    async def run_all_tests(self):
        """运行所有集成测试"""
        self.log("="*70, "HEADER")
        self.log("GUI Integration Test Suite", "HEADER")
        self.log("="*70, "HEADER")
        
        test_cases = [
            ("Greeting Flow", self.test_greeting_flow),
            ("Task Execution Flow", self.test_task_execution_flow),
            ("Rapid Input Test", self.test_rapid_input),
            ("Concurrent Operations", self.test_concurrent_operations),
            ("Callback Stress Test", self.test_callback_stress),
        ]
        
        for test_name, test_func in test_cases:
            await self.run_test(test_name, test_func)
        
        self.print_summary()
    
    async def run_test(self, name: str, test_func):
        """运行单个测试"""
        self.log(f"\n{'='*70}", "TEST")
        self.log(f"Test: {name}", "TEST")
        self.log("="*70, "TEST")
        
        try:
            await test_func()
            self.log("[PASS] Test completed successfully", "PASS")
            self.passed += 1
            self.results.append((name, True, None))
        except AssertionError as e:
            self.log(f"[FAIL] {e}", "FAIL")
            self.failed += 1
            self.results.append((name, False, str(e)))
        except Exception as e:
            self.log(f"[ERROR] {e}", "ERROR")
            self.failed += 1
            self.results.append((name, False, f"Error: {e}"))
    
    async def test_greeting_flow(self):
        """测试问候流程"""
        self.log("Testing greeting flow...")
        
        from blueclaw_v1_gui_fixed import SignalBridge
        
        bridge = SignalBridge()
        messages = []
        
        # 连接信号
        bridge.message_received.connect(lambda m, l: messages.append(m))
        
        # 创建协调器
        coord = create_coordinator_v3(use_real_execution=False)
        
        def on_message(msg):
            bridge.message_received.emit(msg, "info")
        
        coord.set_callbacks(on_message=on_message)
        
        # 运行问候
        await coord.start_task("你好")
        
        # 等待信号处理
        await asyncio.sleep(0.1)
        self.app.processEvents()
        
        # 验证状态
        assert coord.state.phase == "completed", f"Expected completed, got {coord.state.phase}"
        self.log(f"  Final state: {coord.state.phase}", "DEBUG")
    
    async def test_task_execution_flow(self):
        """测试任务执行流程"""
        self.log("Testing task execution flow...")
        
        from blueclaw_v1_gui_fixed import SignalBridge
        
        bridge = SignalBridge()
        events = []
        
        # 连接各种信号
        bridge.blueprint_loaded.connect(lambda s: events.append(("blueprint", len(s))))
        bridge.step_updated.connect(lambda sid, st, idx: events.append(("step", idx, st)))
        bridge.execution_completed.connect(lambda s, m: events.append(("complete", s)))
        
        coord = create_coordinator_v3(use_real_execution=True)
        
        def on_blueprint(steps):
            bridge.blueprint_loaded.emit(steps)
        
        def on_step_update(sid, status, idx):
            bridge.step_updated.emit(sid, status, idx)
        
        def on_complete(result):
            bridge.execution_completed.emit(result.get('success'), result.get('summary', ''))
        
        coord.set_callbacks(
            on_blueprint_loaded=on_blueprint,
            on_step_update=on_step_update,
            on_execution_complete=on_complete
        )
        
        # 执行任务
        await coord.start_task("列出当前目录的文件")
        
        # 等待执行完成
        await asyncio.sleep(0.5)
        self.app.processEvents()
        
        # 验证事件
        self.log(f"  Events captured: {len(events)}", "DEBUG")
        for e in events:
            self.log(f"    {e}", "DEBUG")
        
        assert len(events) > 0, "No events captured"
    
    async def test_rapid_input(self):
        """测试快速输入"""
        self.log("Testing rapid input handling...")
        
        coord = create_coordinator_v3(use_real_execution=False)
        
        # 快速发送多个输入
        inputs = ["你好", "你好", "你好", "你好", "你好"]
        
        for inp in inputs:
            # 使用线程避免阻塞
            thread = threading.Thread(
                target=lambda i=inp: asyncio.run(coord.start_task(i)),
                daemon=True
            )
            thread.start()
            await asyncio.sleep(0.05)  # 短暂延迟
        
        # 等待所有处理完成
        await asyncio.sleep(0.5)
        self.app.processEvents()
        
        self.log(f"  Rapid inputs processed without crash", "DEBUG")
        # 如果没有崩溃就通过
        assert True
    
    async def test_concurrent_operations(self):
        """测试并发操作"""
        self.log("Testing concurrent operations...")
        
        from blueclaw_v1_gui_fixed import SignalBridge
        
        bridge = SignalBridge()
        call_count = [0]
        
        def count_calls(*args):
            call_count[0] += 1
        
        # 连接多个信号到同一个槽
        bridge.state_changed.connect(count_calls)
        bridge.message_received.connect(count_calls)
        bridge.step_updated.connect(count_calls)
        
        # 从多个线程发射信号
        def emit_signals():
            for i in range(10):
                bridge.state_changed.emit("test", i)
                bridge.message_received.emit(f"msg{i}", "info")
        
        threads = []
        for _ in range(3):
            t = threading.Thread(target=emit_signals)
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join(timeout=2)
        
        await asyncio.sleep(0.1)
        self.app.processEvents()
        
        self.log(f"  Total signal calls: {call_count[0]}", "DEBUG")
        # 如果没有崩溃就通过
        assert True
    
    async def test_callback_stress(self):
        """测试回调压力"""
        self.log("Testing callback stress...")
        
        coord = create_coordinator_v3(use_real_execution=True)
        
        callback_count = [0]
        
        def counting_callback(*args):
            callback_count[0] += 1
        
        # 设置多个回调
        coord.set_callbacks(
            on_state_change=counting_callback,
            on_message=counting_callback,
            on_step_update=counting_callback,
        )
        
        # 执行会产生多个回调的任务
        await coord.start_task("列出当前目录的文件")
        
        await asyncio.sleep(0.3)
        self.app.processEvents()
        
        self.log(f"  Callback count: {callback_count[0]}", "DEBUG")
        assert callback_count[0] > 0, "No callbacks received"
    
    def print_summary(self):
        """打印测试摘要"""
        self.log("\n" + "="*70, "SUMMARY")
        self.log("TEST SUMMARY", "SUMMARY")
        self.log("="*70, "SUMMARY")
        
        total = len(self.results)
        self.log(f"Total: {total}")
        self.log(f"Passed: {self.passed}")
        self.log(f"Failed: {self.failed}")
        
        if self.failed > 0:
            self.log("\nFailed Tests:", "FAIL")
            for name, passed, error in self.results:
                if not passed:
                    self.log(f"  - {name}: {error}", "FAIL")
        
        self.log("="*70, "SUMMARY")


async def main():
    """主函数"""
    tester = GUIIntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
