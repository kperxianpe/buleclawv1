#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
blueclaw_v1_gui_fixed.py - Blueclaw v1.0 PyQt5 GUI (Thread-Safe Version)

Fixed:
- All GUI updates now use QTimer.singleShot to ensure thread safety
- Callbacks from background threads safely update UI
"""

import sys
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

# PyQt5 imports
try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QSplitter, QTextEdit, QLineEdit, QPushButton, QLabel, QFrame,
        QScrollArea, QGridLayout, QDialog, QDialogButtonBox,
        QRadioButton, QButtonGroup, QProgressBar, QMessageBox
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
    from PyQt5.QtGui import QFont
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("PyQt5 not available. Install: pip install PyQt5")
    sys.exit(1)

from blueclaw import create_coordinator_v3


# ==================== Styles ====================

STYLESHEET = """
QMainWindow {
    background-color: #f5f5f5;
}
QWidget#chat_panel {
    background-color: #ffffff;
    border-right: 1px solid #e0e0e0;
}
QWidget#canvas_panel {
    background-color: #fafafa;
}
QWidget#vision_panel {
    background-color: #ffffff;
    border-left: 1px solid #e0e0e0;
}
QTextEdit#chat_history {
    background-color: #ffffff;
    border: none;
    font-family: "Microsoft YaHei", "SimHei", sans-serif;
    font-size: 13px;
}
QTextEdit#log_viewer {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: none;
    font-family: "Consolas", "Monaco", monospace;
    font-size: 11px;
}
QLineEdit#input_field {
    border: 2px solid #e0e0e0;
    border-radius: 20px;
    padding: 8px 15px;
    font-size: 13px;
    background-color: #f5f5f5;
}
QLineEdit#input_field:focus {
    border-color: #2196f3;
    background-color: #ffffff;
}
QPushButton#send_btn {
    background-color: #2196f3;
    color: white;
    border: none;
    border-radius: 20px;
    padding: 8px 20px;
    font-weight: bold;
}
QPushButton#send_btn:hover {
    background-color: #1976d2;
}
QPushButton#action_btn {
    background-color: #f5f5f5;
    border: 1px solid #e0e0e0;
    border-radius: 15px;
    padding: 5px 15px;
    font-size: 12px;
}
QPushButton#action_btn:hover {
    background-color: #e0e0e0;
}
QLabel#header {
    font-size: 14px;
    font-weight: bold;
    color: #333;
    padding: 10px;
}
"""


# ==================== Signal Bridge ====================

class SignalBridge(QObject):
    """Bridge to safely emit signals from background threads"""
    
    # Signals for UI updates
    state_changed = pyqtSignal(str, int)  # phase, progress
    message_received = pyqtSignal(str, str)  # message, level
    execution_preview = pyqtSignal(object)  # preview object
    question_received = pyqtSignal(object)  # question object
    options_received = pyqtSignal(list)  # options list
    blueprint_loaded = pyqtSignal(list)  # steps list
    step_updated = pyqtSignal(str, str, int)  # step_id, status, index
    execution_completed = pyqtSignal(bool, str)  # success, summary
    intervention_needed = pyqtSignal(str, str)  # step_id, reason


# ==================== Step Widget ====================

class StepWidget(QFrame):
    """Execution step widget"""
    
    def __init__(self, index: int, name: str, description: str = "", parent=None):
        super().__init__(parent)
        self.index = index
        self.step_id = f"step_{index}"
        self.name = name
        self.description = description
        self.status = "pending"
        
        self.setObjectName("step_frame")
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Status icon
        self.icon_label = QLabel("⏳")
        self.icon_label.setFont(QFont("Segoe UI Emoji", 20))
        layout.addWidget(self.icon_label)
        
        # Content
        content = QVBoxLayout()
        content.setSpacing(3)
        
        self.title_label = QLabel(f"步骤 {self.index + 1}: {self.name}")
        self.title_label.setFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        content.addWidget(self.title_label)
        
        if self.description:
            self.desc_label = QLabel(self.description)
            self.desc_label.setFont(QFont("Microsoft YaHei", 9))
            self.desc_label.setStyleSheet("color: #666;")
            content.addWidget(self.desc_label)
        
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("color: #666; font-size: 11px;")
        self.result_label.hide()
        content.addWidget(self.result_label)
        
        layout.addLayout(content, 1)
    
    def set_status(self, status: str, result: str = None):
        """Update step status"""
        self.status = status
        
        icons = {
            "pending": "⏳", "running": "🔄", "completed": "✅",
            "failed": "❌", "paused": "⏸️", "skipped": "⏭️"
        }
        self.icon_label.setText(icons.get(status, "❓"))
        
        # Update border color based on status
        colors = {
            "pending": "#e0e0e0", "running": "#2196f3",
            "completed": "#4caf50", "failed": "#f44336", "paused": "#ff9800"
        }
        color = colors.get(status, "#e0e0e0")
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        
        if result:
            self.result_label.setText(result)
            self.result_label.show()


# ==================== Main Window ====================

class BlueclawMainWindow(QMainWindow):
    """Blueclaw v1.0 Main Window (Thread-Safe)"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blueclaw v1.0 - AI Self-Operating Canvas")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create signal bridge for thread-safe UI updates
        self.signal_bridge = SignalBridge()
        self._connect_signals()
        
        # Initialize coordinator
        self.coordinator = create_coordinator_v3(use_real_execution=True)
        self.setup_callbacks()
        
        # Step widgets storage
        self.step_widgets: Dict[str, StepWidget] = {}
        
        self._setup_ui()
        self._add_welcome_message()
    
    def _connect_signals(self):
        """Connect signal bridge to UI handlers"""
        self.signal_bridge.state_changed.connect(self._handle_state_change)
        self.signal_bridge.message_received.connect(self._handle_message)
        self.signal_bridge.execution_preview.connect(self._handle_execution_preview)
        self.signal_bridge.question_received.connect(self._handle_question)
        self.signal_bridge.options_received.connect(self._handle_options)
        self.signal_bridge.blueprint_loaded.connect(self._handle_blueprint_loaded)
        self.signal_bridge.step_updated.connect(self._handle_step_update)
        self.signal_bridge.execution_completed.connect(self._handle_execution_complete)
        self.signal_bridge.intervention_needed.connect(self._handle_intervention_needed)
    
    def setup_callbacks(self):
        """Setup coordinator callbacks - emit signals for thread safety"""
        def on_state_change(state):
            self.signal_bridge.state_changed.emit(state.phase, state.progress)
        
        def on_message(msg):
            self.signal_bridge.message_received.emit(msg, "info")
        
        def on_execution_preview(preview):
            self.signal_bridge.execution_preview.emit(preview)
        
        def on_question(question):
            self.signal_bridge.question_received.emit(question)
        
        def on_options(options):
            self.signal_bridge.options_received.emit(options)
        
        def on_blueprint_loaded(steps):
            self.signal_bridge.blueprint_loaded.emit(steps)
        
        def on_step_update(step_id, status, index):
            self.signal_bridge.step_updated.emit(step_id, status, index)
        
        def on_execution_complete(result):
            self.signal_bridge.execution_completed.emit(
                result.get('success', False),
                result.get('summary', 'Completed')
            )
        
        def on_intervention_needed(step_id, reason):
            self.signal_bridge.intervention_needed.emit(step_id, reason)
        
        self.coordinator.set_callbacks(
            on_state_change=on_state_change,
            on_message=on_message,
            on_execution_preview=on_execution_preview,
            on_question=on_question,
            on_options=on_options,
            on_blueprint_loaded=on_blueprint_loaded,
            on_step_update=on_step_update,
            on_execution_complete=on_execution_complete,
            on_intervention_needed=on_intervention_needed
        )
    
    def _setup_ui(self):
        """Setup UI components"""
        self.setStyleSheet(STYLESHEET)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left Panel: Chat
        self.chat_panel = self._create_chat_panel()
        splitter.addWidget(self.chat_panel)
        
        # Center Panel: Canvas
        self.canvas_panel = self._create_canvas_panel()
        splitter.addWidget(self.canvas_panel)
        
        # Right Panel: Log
        self.vision_panel = self._create_vision_panel()
        splitter.addWidget(self.vision_panel)
        
        splitter.setSizes([420, 700, 280])
        
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪 | 模式: 真实执行")
    
    def _create_chat_panel(self) -> QWidget:
        """Create chat panel"""
        panel = QWidget()
        panel.setObjectName("chat_panel")
        panel.setMinimumWidth(300)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QLabel("💬 对话")
        header.setObjectName("header")
        layout.addWidget(header)
        
        self.chat_history = QTextEdit()
        self.chat_history.setObjectName("chat_history")
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)
        
        input_frame = QFrame()
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        self.input_field = QLineEdit()
        self.input_field.setObjectName("input_field")
        self.input_field.setPlaceholderText("输入你的任务...")
        self.input_field.returnPressed.connect(self.on_send)
        input_layout.addWidget(self.input_field)
        
        send_btn = QPushButton("发送")
        send_btn.setObjectName("send_btn")
        send_btn.clicked.connect(self.on_send)
        input_layout.addWidget(send_btn)
        
        layout.addWidget(input_frame)
        
        quick_frame = QFrame()
        quick_layout = QHBoxLayout(quick_frame)
        quick_layout.setContentsMargins(10, 0, 10, 10)
        
        quick_tasks = [
            ("规划旅行", "我想规划一个周末短途旅行"),
            ("列文件", "列出当前目录的文件"),
            ("写代码", "写一个Python脚本批量重命名文件"),
        ]
        
        for label, task in quick_tasks:
            btn = QPushButton(label)
            btn.setObjectName("action_btn")
            btn.clicked.connect(lambda checked, t=task: self.quick_task(t))
            quick_layout.addWidget(btn)
        
        layout.addWidget(quick_frame)
        
        return panel
    
    def _create_canvas_panel(self) -> QWidget:
        """Create canvas panel"""
        panel = QWidget()
        panel.setObjectName("canvas_panel")
        panel.setMinimumWidth(400)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header_layout = QHBoxLayout()
        
        header = QLabel("📋 执行蓝图")
        header.setObjectName("header")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        self.pause_btn = QPushButton("⏸️ 暂停")
        self.pause_btn.setObjectName("action_btn")
        self.pause_btn.clicked.connect(self.on_pause)
        header_layout.addWidget(self.pause_btn)
        
        replan_btn = QPushButton("🔄 重新规划")
        replan_btn.setObjectName("action_btn")
        replan_btn.clicked.connect(self.on_replan)
        header_layout.addWidget(replan_btn)
        
        layout.addLayout(header_layout)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.canvas_content = QWidget()
        self.canvas_layout = QVBoxLayout(self.canvas_content)
        self.canvas_layout.setAlignment(Qt.AlignTop)
        self.canvas_layout.setSpacing(10)
        self.canvas_layout.setContentsMargins(15, 15, 15, 15)
        
        self.canvas_placeholder = QLabel(
            "执行蓝图将在这里显示\n\n开始一个任务来查看执行流程"
        )
        self.canvas_placeholder.setAlignment(Qt.AlignCenter)
        self.canvas_placeholder.setStyleSheet("color: #999; font-size: 14px; padding: 50px;")
        self.canvas_layout.addWidget(self.canvas_placeholder)
        
        scroll.setWidget(self.canvas_content)
        layout.addWidget(scroll)
        
        return panel
    
    def _create_vision_panel(self) -> QWidget:
        """Create vision/log panel"""
        panel = QWidget()
        panel.setObjectName("vision_panel")
        panel.setMinimumWidth(200)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QLabel("📜 日志")
        header.setObjectName("header")
        layout.addWidget(header)
        
        self.log_viewer = QTextEdit()
        self.log_viewer.setObjectName("log_viewer")
        self.log_viewer.setReadOnly(True)
        layout.addWidget(self.log_viewer)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        return panel
    
    def _add_welcome_message(self):
        """Add welcome message"""
        welcome = """<h2>🤖 Blueclaw v1.0</h2>
<p>AI Self-Operating Canvas Framework</p>
<hr>
<p><b>我可以帮你：</b></p>
<ul>
<li>✈️ 规划旅行行程</li>
<li>📁 执行文件操作</li>
<li>🐍 编写Python代码</li>
<li>🔍 搜索网络信息</li>
</ul>
<p>请输入你想做什么...</p>"""
        self.add_chat_message("ai", welcome)
    
    # ==================== Event Handlers ====================
    
    def on_send(self):
        """Handle send button"""
        text = self.input_field.text().strip()
        if not text:
            return
        
        self.input_field.clear()
        self.add_chat_message("user", text)
        
        # Run task in background thread
        thread = threading.Thread(
            target=lambda: asyncio.run(self.coordinator.start_task(text)),
            daemon=True
        )
        thread.start()
    
    def quick_task(self, task: str):
        """Quick task button"""
        self.input_field.setText(task)
        self.on_send()
    
    def on_pause(self):
        """Pause/Resume execution"""
        if self.coordinator.execution_system.is_paused:
            self.coordinator.execution_system.resume_execution()
            self.pause_btn.setText("⏸️ 暂停")
        else:
            self.coordinator.execution_system.pause_execution()
            self.pause_btn.setText("▶️ 继续")
    
    def on_replan(self):
        """Replan from current step"""
        reply = QMessageBox.question(
            self, "重新规划",
            "确定要回退到思考阶段重新规划吗？\n已完成的步骤将保留。",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            thread = threading.Thread(
                target=lambda: asyncio.run(
                    self.coordinator.handle_intervention("replan")
                ),
                daemon=True
            )
            thread.start()
    
    # ==================== Signal Handlers (Main Thread) ====================
    
    def _handle_state_change(self, phase: str, progress: int):
        """Handle state change"""
        self.status_bar.showMessage(f"状态: {phase} | 进度: {progress}% | 模式: real")
        self.progress_bar.setValue(progress)
    
    def _handle_message(self, msg: str, level: str):
        """Handle log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_viewer.append(f"[{timestamp}] {msg}")
        scrollbar = self.log_viewer.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _handle_execution_preview(self, preview):
        """Handle execution preview"""
        steps_count = len(preview.steps) if hasattr(preview, 'steps') else 0
        text = f"<b>📋 执行计划 ({steps_count} 个步骤)</b><br>"
        for i, step in enumerate(preview.steps if hasattr(preview, 'steps') else []):
            name = step.get('name', '未命名') if isinstance(step, dict) else getattr(step, 'name', '未命名')
            text += f"{i+1}. {name}<br>"
        self.add_chat_message("ai", text)
    
    def _handle_question(self, question):
        """Handle clarification question"""
        text = f"{question.text}<br><br>"
        if question.options:
            for opt in question.options:
                text += f"[{opt['id']}] {opt['label']}<br>"
        self.add_chat_message("ai", text)
    
    def _handle_options(self, options):
        """Handle options"""
        text = "请选择执行方案:<br><br>"
        for opt in options:
            default = " (推荐)" if opt.is_default else ""
            text += f"[{opt.id}] {opt.label}{default}<br>"
        self.add_chat_message("ai", text)
    
    def _handle_blueprint_loaded(self, steps):
        """Handle blueprint loaded"""
        self.clear_canvas()
        for i, step in enumerate(steps):
            widget = StepWidget(index=i, name=step.name, description=step.description)
            self.step_widgets[widget.step_id] = widget
            self.canvas_layout.addWidget(widget)
    
    def _handle_step_update(self, step_id: str, status: str, index: int):
        """Handle step update"""
        if step_id in self.step_widgets:
            self.step_widgets[step_id].set_status(status)
        elif f"step_{index}" in self.step_widgets:
            self.step_widgets[f"step_{index}"].set_status(status)
    
    def _handle_execution_complete(self, success: bool, summary: str):
        """Handle execution complete"""
        icon = "✅" if success else "❌"
        self.add_chat_message("ai", f"<h3>{icon} {summary}</h3>")
        QMessageBox.information(self, "执行完成", summary)
    
    def _handle_intervention_needed(self, step_id: str, reason: str):
        """Handle intervention needed"""
        reply = QMessageBox.question(
            self, "需要干预",
            f"{reason}<br><br>是否回退到思考阶段重新规划？",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            thread = threading.Thread(
                target=lambda: asyncio.run(
                    self.coordinator.handle_intervention("replan")
                ),
                daemon=True
            )
            thread.start()
    
    # ==================== Helper Methods ====================
    
    def add_chat_message(self, role: str, text: str):
        """Add chat message"""
        if role == "user":
            html = f'<p style="color: #0066cc; margin: 8px 0;"><b>你:</b> {text}</p>'
        elif role == "ai":
            html = f'<p style="color: #333; margin: 8px 0;"><b>AI:</b> {text}</p>'
        else:
            html = f'<p style="color: #666; margin: 8px 0; font-size: 11px;"><i>[系统] {text}</i></p>'
        
        self.chat_history.insertHtml(html)
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_canvas(self):
        """Clear canvas"""
        for widget in self.step_widgets.values():
            widget.deleteLater()
        self.step_widgets.clear()
        self.canvas_placeholder.show()


def main():
    """Main entry"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    window = BlueclawMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
