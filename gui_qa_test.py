#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gui_qa_test.py - Comprehensive Q&A Test for Blueclaw GUI

Tests various conversation scenarios in GUI mode.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QLineEdit, QPushButton, QLabel, QScrollArea,
    QFrame, QSplitter, QListWidget, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QColor

from blueclaw import create_coordinator_v3


class QATestRunner(QThread):
    """Background test runner"""
    
    log_signal = pyqtSignal(str, str)  # message, type
    step_signal = pyqtSignal(int, str)  # step_index, status
    complete_signal = pyqtSignal(bool, str)  # success, summary
    
    def __init__(self, coordinator, test_cases):
        super().__init__()
        self.coordinator = coordinator
        self.test_cases = test_cases
        self.current_test = 0
    
    def run(self):
        """Run all tests"""
        asyncio.run(self.run_tests())
    
    async def run_tests(self):
        """Run test cases"""
        for i, (test_input, expected_behavior) in enumerate(self.test_cases):
            self.current_test = i
            self.log_signal.emit(f"\n{'='*60}", "header")
            self.log_signal.emit(f"Test {i+1}/{len(self.test_cases)}: {test_input}", "header")
            self.log_signal.emit(f"Expected: {expected_behavior}", "info")
            self.log_signal.emit("="*60, "header")
            
            await self.run_single_test(test_input)
            
            # Small delay between tests
            await asyncio.sleep(0.5)
        
        self.complete_signal.emit(True, f"Completed {len(self.test_cases)} tests")
    
    async def run_single_test(self, test_input: str):
        """Run single test"""
        try:
            await self.coordinator.start_task(test_input)
            
            state = self.coordinator.state.phase
            self.log_signal.emit(f"Final state: {state}", "info")
            
            if state == "completed":
                self.log_signal.emit("✓ Test completed successfully", "success")
            elif state == "executing":
                self.log_signal.emit("✓ Task is executing", "success")
            elif state == "thinking":
                self.log_signal.emit("? Waiting for user input", "warning")
            else:
                self.log_signal.emit(f"? Unexpected state: {state}", "warning")
                
        except Exception as e:
            self.log_signal.emit(f"✗ Error: {e}", "error")


class QATestWindow(QMainWindow):
    """Q&A Test Window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blueclaw v1.0 - Q&A Comprehensive Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize coordinator
        self.coordinator = create_coordinator_v3(use_real_execution=True)
        self.setup_callbacks()
        
        # Test cases
        self.test_cases = [
            # Greetings
            ("你好", "Should greet user"),
            ("Hello", "Should greet in English"),
            ("Hi", "Should greet"),
            ("在吗", "Should respond to presence check"),
            
            # Identity questions
            ("你是谁", "Should introduce itself"),
            ("你是什么", "Should explain what it is"),
            ("who are you", "Should introduce in English"),
            
            # Capability questions
            ("你能做什么", "Should list capabilities"),
            ("你会什么", "Should list skills"),
            ("what can you do", "Should list in English"),
            ("help", "Should show help"),
            
            # Task - File operations
            ("列出当前目录的文件", "Should execute file listing"),
            ("显示当前文件夹内容", "Should show folder contents"),
            ("获取目录列表", "Should get directory list"),
            
            # Task - Travel planning
            ("我想规划周末旅行", "Should provide travel options"),
            ("规划去杭州的旅行", "Should create travel blueprint"),
            ("推荐短途旅游目的地", "Should suggest destinations"),
            
            # Task - Code generation
            ("写一个Python脚本", "Should generate code blueprint"),
            ("批量重命名图片文件", "Should create rename script"),
            ("写计算斐波那契的函数", "Should generate function"),
            
            # Edge cases
            ("???", "Should handle unknown input gracefully"),
            ("123456", "Should handle numeric input"),
            ("", "Should handle empty input"),
        ]
        
        self._setup_ui()
        self.log("Q&A Test Suite initialized")
        self.log(f"Total test cases: {len(self.test_cases)}")
    
    def setup_callbacks(self):
        """Setup coordinator callbacks"""
        self.coordinator.set_callbacks(
            on_state_change=self.on_state_change,
            on_message=self.on_log_message,
            on_execution_preview=self.on_execution_preview,
            on_question=self.on_question,
            on_options=self.on_options,
            on_blueprint_loaded=self.on_blueprint_loaded,
            on_step_update=self.on_step_update,
            on_execution_complete=self.on_execution_complete,
            on_intervention_needed=self.on_intervention_needed
        )
    
    def _setup_ui(self):
        """Setup UI"""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Left panel - Test list
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        left_layout.addWidget(QLabel("📋 Test Cases"))
        
        self.test_list = QListWidget()
        for i, (test_input, _) in enumerate(self.test_cases):
            self.test_list.addItem(f"{i+1}. {test_input[:30]}...")
        self.test_list.itemClicked.connect(self.on_test_selected)
        left_layout.addWidget(self.test_list)
        
        # Control buttons
        btn_layout = QHBoxLayout()
        
        self.run_all_btn = QPushButton("▶ Run All Tests")
        self.run_all_btn.clicked.connect(self.run_all_tests)
        btn_layout.addWidget(self.run_all_btn)
        
        self.run_one_btn = QPushButton("▶ Run Selected")
        self.run_one_btn.clicked.connect(self.run_selected_test)
        btn_layout.addWidget(self.run_one_btn)
        
        left_layout.addLayout(btn_layout)
        
        # Progress
        self.progress = QProgressBar()
        self.progress.setMaximum(len(self.test_cases))
        self.progress.setValue(0)
        left_layout.addWidget(self.progress)
        
        layout.addWidget(left_panel, 1)
        
        # Right panel - Results
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        right_layout.addWidget(QLabel("📝 Test Results"))
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setFont(QFont("Consolas", 10))
        right_layout.addWidget(self.results_text)
        
        # Input for manual test
        right_layout.addWidget(QLabel("💬 Manual Test Input:"))
        
        input_layout = QHBoxLayout()
        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("Enter test input...")
        self.manual_input.returnPressed.connect(self.run_manual_test)
        input_layout.addWidget(self.manual_input)
        
        self.manual_btn = QPushButton("Send")
        self.manual_btn.clicked.connect(self.run_manual_test)
        input_layout.addWidget(self.manual_btn)
        
        right_layout.addLayout(input_layout)
        
        layout.addWidget(right_panel, 2)
    
    def log(self, message: str, msg_type: str = "info"):
        """Log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        colors = {
            "header": "#2196f3",
            "success": "#4caf50",
            "error": "#f44336",
            "warning": "#ff9800",
            "info": "#333333"
        }
        
        color = colors.get(msg_type, "#333333")
        html = f'<span style="color: #666;">[{timestamp}]</span> <span style="color: {color};">{message}</span><br>'
        
        self.results_text.insertHtml(html)
        self.results_text.verticalScrollBar().setValue(
            self.results_text.verticalScrollBar().maximum()
        )
    
    # ==================== Callback Handlers ====================
    
    def on_state_change(self, state):
        """Handle state change"""
        self.log(f"State changed: {state.phase} ({state.progress}%)", "info")
    
    def on_log_message(self, msg: str):
        """Handle log message"""
        if '[INIT]' not in msg:
            self.log(msg, "info")
    
    def on_execution_preview(self, preview):
        """Handle execution preview"""
        steps_count = len(preview.steps) if hasattr(preview, 'steps') else 0
        self.log(f"Execution preview: {steps_count} steps", "success")
    
    def on_question(self, question):
        """Handle question"""
        self.log(f"Question: {question.text}", "warning")
        if question.options:
            for opt in question.options:
                self.log(f"  [{opt['id']}] {opt['label']}", "info")
    
    def on_options(self, options):
        """Handle options"""
        self.log(f"Options provided ({len(options)}):", "warning")
        for opt in options:
            default = " (default)" if opt.is_default else ""
            self.log(f"  [{opt.id}] {opt.label}{default}", "info")
    
    def on_blueprint_loaded(self, steps):
        """Handle blueprint loaded"""
        self.log(f"Blueprint loaded: {len(steps)} steps", "success")
    
    def on_step_update(self, step_id, status, index):
        """Handle step update"""
        self.log(f"Step {index+1}: {status}", "info")
    
    def on_execution_complete(self, result):
        """Handle execution complete"""
        success = "✓" if result.get('success') else "✗"
        self.log(f"{success} Execution complete: {result.get('summary')}", 
                "success" if result.get('success') else "error")
    
    def on_intervention_needed(self, step_id, reason):
        """Handle intervention"""
        self.log(f"Intervention needed: {reason}", "warning")
    
    # ==================== Test Actions ====================
    
    def on_test_selected(self, item):
        """Handle test selection"""
        index = self.test_list.row(item)
        test_input, expected = self.test_cases[index]
        self.manual_input.setText(test_input)
        self.log(f"Selected test {index+1}: {test_input}", "info")
        self.log(f"Expected: {expected}", "info")
    
    def run_all_tests(self):
        """Run all tests"""
        self.log("\n" + "="*60, "header")
        self.log("Starting comprehensive Q&A test suite", "header")
        self.log("="*60, "header")
        
        self.run_all_btn.setEnabled(False)
        self.progress.setValue(0)
        
        # Create new coordinator for tests
        self.test_coordinator = create_coordinator_v3(use_real_execution=True)
        self.setup_callbacks()
        
        # Create and start test runner
        self.test_runner = QATestRunner(self.test_coordinator, self.test_cases)
        self.test_runner.log_signal.connect(self.on_test_log)
        self.test_runner.step_signal.connect(self.on_test_step)
        self.test_runner.complete_signal.connect(self.on_test_complete)
        self.test_runner.start()
    
    def on_test_log(self, message, msg_type):
        """Handle test log"""
        self.log(message, msg_type)
    
    def on_test_step(self, step_index, status):
        """Handle test step"""
        self.progress.setValue(step_index + 1)
    
    def on_test_complete(self, success, summary):
        """Handle test completion"""
        self.log("\n" + "="*60, "header")
        self.log(f"Test Suite Complete: {summary}", "success" if success else "error")
        self.log("="*60, "header")
        self.run_all_btn.setEnabled(True)
    
    def run_selected_test(self):
        """Run selected test"""
        current_row = self.test_list.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "No Selection", "Please select a test case")
            return
        
        test_input, expected = self.test_cases[current_row]
        self.run_manual_test_with_input(test_input)
    
    def run_manual_test(self):
        """Run manual test"""
        text = self.manual_input.text().strip()
        if not text:
            return
        self.run_manual_test_with_input(text)
    
    def run_manual_test_with_input(self, test_input: str):
        """Run test with specific input"""
        self.log(f"\n[Manual Test] Input: '{test_input}'", "header")
        
        # Run in background thread
        import threading
        def run_test():
            try:
                asyncio.run(self.coordinator.start_task(test_input))
            except Exception as e:
                self.log(f"Error: {e}", "error")
        
        thread = threading.Thread(target=run_test, daemon=True)
        thread.start()


def main():
    """Main entry"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set font
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    window = QATestWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
