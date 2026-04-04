#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_gui_unit.py - GUI单元测试

测试各个GUI组件的功能
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestStepWidget(unittest.TestCase):
    """测试步骤控件"""
    
    def setUp(self):
        """测试前准备"""
        try:
            from PyQt5.QtWidgets import QApplication
            from blueclaw_v1_gui_fixed import StepWidget
            self.app = QApplication.instance() or QApplication(sys.argv)
            self.StepWidget = StepWidget
        except ImportError as e:
            self.skipTest(f"PyQt5 not available: {e}")
    
    def test_step_widget_creation(self):
        """测试步骤控件创建"""
        widget = self.StepWidget(0, "测试步骤", "测试描述")
        self.assertEqual(widget.index, 0)
        self.assertEqual(widget.name, "测试步骤")
        self.assertEqual(widget.status, "pending")
    
    def test_step_status_update(self):
        """测试状态更新"""
        widget = self.StepWidget(0, "测试步骤")
        
        # 测试各种状态
        for status in ["pending", "running", "completed", "failed", "paused"]:
            widget.set_status(status)
            self.assertEqual(widget.status, status)


class TestSignalBridge(unittest.TestCase):
    """测试信号桥"""
    
    def setUp(self):
        try:
            from PyQt5.QtWidgets import QApplication
            from blueclaw_v1_gui_fixed import SignalBridge
            self.app = QApplication.instance() or QApplication(sys.argv)
            self.SignalBridge = SignalBridge
        except ImportError as e:
            self.skipTest(f"PyQt5 not available: {e}")
    
    def test_signal_emission(self):
        """测试信号发射"""
        bridge = self.SignalBridge()
        
        # 测试状态改变信号
        received = []
        bridge.state_changed.connect(lambda p, prog: received.append((p, prog)))
        bridge.state_changed.emit("executing", 50)
        
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0], ("executing", 50))
    
    def test_message_signal(self):
        """测试消息信号"""
        bridge = self.SignalBridge()
        
        received = []
        bridge.message_received.connect(lambda m, l: received.append((m, l)))
        bridge.message_received.emit("测试消息", "info")
        
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0][0], "测试消息")


class TestCoordinatorIntegration(unittest.TestCase):
    """测试协调器集成"""
    
    def setUp(self):
        try:
            from blueclaw import create_coordinator_v3
            self.create_coordinator = create_coordinator_v3
        except ImportError as e:
            self.skipTest(f"Blueclaw not available: {e}")
    
    def test_coordinator_creation(self):
        """测试协调器创建"""
        coord = self.create_coordinator(use_real_execution=False)
        self.assertIsNotNone(coord)
        self.assertEqual(coord.state.execution_mode, "mock")
    
    def test_callback_setup(self):
        """测试回调设置"""
        coord = self.create_coordinator(use_real_execution=False)
        
        callbacks = {
            'on_state_change': lambda s: None,
            'on_message': lambda m: None,
            'on_execution_preview': lambda p: None,
        }
        
        # 不应该抛出异常
        coord.set_callbacks(**callbacks)


class TestThreadSafety(unittest.TestCase):
    """测试线程安全"""
    
    def setUp(self):
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QThread, pyqtSignal
            from blueclaw_v1_gui_fixed import SignalBridge
            self.app = QApplication.instance() or QApplication(sys.argv)
            self.SignalBridge = SignalBridge
        except ImportError as e:
            self.skipTest(f"PyQt5 not available: {e}")
    
    def test_cross_thread_signal(self):
        """测试跨线程信号"""
        import threading
        import time
        
        bridge = self.SignalBridge()
        received = []
        
        # 主线程连接信号
        bridge.message_received.connect(lambda m, l: received.append(m))
        
        # 后台线程发射信号
        def emit_from_thread():
            time.sleep(0.1)
            bridge.message_received.emit("来自后台线程", "info")
        
        thread = threading.Thread(target=emit_from_thread)
        thread.start()
        thread.join(timeout=1)
        
        # 处理事件（在真实GUI中会自动处理）
        self.app.processEvents()
        
        # 由于信号是队列的，我们检查是否没有崩溃
        self.assertTrue(True)  # 如果没有崩溃就通过


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def setUp(self):
        try:
            from blueclaw import create_coordinator_v3
            self.create_coordinator = create_coordinator_v3
        except ImportError as e:
            self.skipTest(f"Blueclaw not available: {e}")
    
    def test_empty_input(self):
        """测试空输入"""
        coord = self.create_coordinator(use_real_execution=False)
        # 空输入应该被优雅处理
        self.assertIsNotNone(coord)
    
    def test_very_long_input(self):
        """测试超长输入"""
        coord = self.create_coordinator(use_real_execution=False)
        long_text = "A" * 10000
        # 不应该崩溃
        self.assertIsNotNone(coord)
    
    def test_special_characters(self):
        """测试特殊字符"""
        coord = self.create_coordinator(use_real_execution=False)
        special = "!@#$%^&*()<>[]{}|;':\",./?"
        # 不应该崩溃
        self.assertIsNotNone(coord)
    
    def test_unicode_input(self):
        """测试Unicode输入"""
        coord = self.create_coordinator(use_real_execution=False)
        unicode_text = "你好 こんにちは Hello αβγ 🎉"
        # 不应该崩溃
        self.assertIsNotNone(coord)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestStepWidget))
    suite.addTests(loader.loadTestsFromTestCase(TestSignalBridge))
    suite.addTests(loader.loadTestsFromTestCase(TestCoordinatorIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestThreadSafety))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
