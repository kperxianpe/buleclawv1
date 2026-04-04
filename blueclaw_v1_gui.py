#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
blueclaw_v1_gui.py - Blueclaw v1.0 PyQt5 GUI

Layout:
- Left (30%): Chat Panel
- Center (50%): Canvas Execution Blueprint
- Right (20%): AI Vision / Log Panel
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
        QScrollArea, QGridLayout, QGroupBox, QStackedWidget, QMessageBox,
        QDialog, QDialogButtonBox, QRadioButton, QButtonGroup, QProgressBar,
        QToolButton, QMenu, QAction, QSystemTrayIcon, QStyle
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
    from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QTextCursor
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
    line-height: 1.5;
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

QPushButton#send_btn:pressed {
    background-color: #0d47a1;
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

QLabel#step_title {
    font-weight: bold;
    font-size: 13px;
    color: #333;
}

QLabel#step_desc {
    font-size: 11px;
    color: #666;
}

QFrame#step_frame {
    background-color: white;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
}

QFrame#step_frame[status="running"] {
    border-color: #2196f3;
    background-color: #e3f2fd;
}

QFrame#step_frame[status="completed"] {
    border-color: #4caf50;
    background-color: #e8f5e9;
}

QFrame#step_frame[status="failed"] {
    border-color: #f44336;
    background-color: #ffebee;
}

QFrame#step_frame[status="paused"] {
    border-color: #ff9800;
    background-color: #fff3e0;
}

QLabel#header {
    font-size: 14px;
    font-weight: bold;
    color: #333;
    padding: 10px;
}
"""


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
        self.setProperty("status", "pending")
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(10)
        
        # Status icon
        self.icon_label = QLabel("⏳")
        self.icon_label.setFont(QFont("Segoe UI Emoji", 20))
        layout.addWidget(self.icon_label)
        
        # Content
        content = QVBoxLayout()
        content.setSpacing(3)
        
        self.title_label = QLabel(f"步骤 {self.index + 1}: {self.name}")
        self.title_label.setObjectName("step_title")
        content.addWidget(self.title_label)
        
        if self.description:
            self.desc_label = QLabel(self.description)
            self.desc_label.setObjectName("step_desc")
            content.addWidget(self.desc_label)
        
        layout.addLayout(content, 1)
        
        # Result label (hidden initially)
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("color: #666; font-size: 11px;")
        self.result_label.hide()
        content.addWidget(self.result_label)
    
    def set_status(self, status: str, result: str = None):
        """Update step status"""
        self.status = status
        self.setProperty("status", status)
        self.style().unpolish(self)
        self.style().polish(self)
        
        icons = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "failed": "❌",
            "paused": "⏸️",
            "skipped": "⏭️"
        }
        self.icon_label.setText(icons.get(status, "❓"))
        
        if result:
            self.result_label.setText(result)
            self.result_label.show()


# ==================== Options Dialog ====================

class OptionsDialog(QDialog):
    """Options selection dialog"""
    
    selected = pyqtSignal(str)
    
    def __init__(self, title: str, options: List[Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择执行方案")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Bold))
        layout.addWidget(title_label)
        
        # Options
        self.button_group = QButtonGroup(self)
        
        for i, opt in enumerate(options):
            radio = QRadioButton(f"[{opt.id}] {opt.label}")
            radio.setFont(QFont("Microsoft YaHei", 12))
            
            if opt.is_default:
                radio.setChecked(True)
            
            desc = QLabel(f"    {opt.description}")
            desc.setStyleSheet("color: #666; margin-left: 20px;")
            
            self.button_group.addButton(radio, i)
            layout.addWidget(radio)
            layout.addWidget(desc)
        
        layout.addSpacing(20)
        
        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        btn_box.accepted.connect(self.on_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)
    
    def on_accept(self):
        checked = self.button_group.checkedButton()
        if checked:
            idx = self.button_group.id(checked)
            self.selected.emit(chr(65 + idx))  # A, B, C...
        self.accept()


# ==================== Question Dialog ====================

class QuestionDialog(QDialog):
    """Question dialog"""
    
    answered = pyqtSignal(str)
    
    def __init__(self, question, parent=None):
        super().__init__(parent)
        self.setWindowTitle("需要更多信息")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Question text
        text_label = QLabel(question.text)
        text_label.setFont(QFont("Microsoft YaHei", 13))
        text_label.setWordWrap(True)
        layout.addWidget(text_label)
        
        # Options if available
        self.answer_input = QLineEdit()
        
        if question.options:
            self.button_group = QButtonGroup(self)
            for opt in question.options:
                radio = QRadioButton(f"[{opt['id']}] {opt['label']}")
                radio.setFont(QFont("Microsoft YaHei", 11))
                desc = QLabel(f"    {opt.get('description', '')}")
                desc.setStyleSheet("color: #666; margin-left: 20px;")
                
                self.button_group.addButton(radio)
                layout.addWidget(radio)
                layout.addWidget(desc)
        else:
            layout.addWidget(self.answer_input)
        
        layout.addSpacing(20)
        
        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(self.on_accept)
        layout.addWidget(btn_box)
    
    def on_accept(self):
        if hasattr(self, 'button_group'):
            checked = self.button_group.checkedButton()
            if checked:
                text = checked.text()
                answer = text[1] if len(text) > 1 and text[0] == '[' else text
                self.answered.emit(answer)
        else:
            self.answered.emit(self.answer_input.text())
        self.accept()


# ==================== Main Window ====================

class BlueclawMainWindow(QMainWindow):
    """Blueclaw v1.0 Main Window"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blueclaw v1.0 - AI Self-Operating Canvas")
        self.setGeometry(100, 100, 1400, 800)
        
        # Initialize coordinator
        self.coordinator = create_coordinator_v3(use_real_execution=True)
        self.setup_callbacks()
        
        # Step widgets storage
        self.step_widgets: Dict[str, StepWidget] = {}
        
        self._setup_ui()
        self._add_welcome_message()
    
    def setup_callbacks(self):
        """Setup coordinator callbacks"""
        self.coordinator.set_callbacks(
            on_state_change=self.on_state_change,
            on_message=self.on_message,
            on_execution_preview=self.on_execution_preview,
            on_question=self.on_question,
            on_options=self.on_options,
            on_blueprint_loaded=self.on_blueprint_loaded,
            on_step_update=self.on_step_update,
            on_execution_complete=self.on_execution_complete,
            on_intervention_needed=self.on_intervention_needed
        )
    
    def _setup_ui(self):
        """Setup UI components"""
        self.setStyleSheet(STYLESHEET)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout with splitter
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # === Left Panel: Chat (30%) ===
        self.chat_panel = self._create_chat_panel()
        splitter.addWidget(self.chat_panel)
        
        # === Center Panel: Canvas (50%) ===
        self.canvas_panel = self._create_canvas_panel()
        splitter.addWidget(self.canvas_panel)
        
        # === Right Panel: Vision/Log (20%) ===
        self.vision_panel = self._create_vision_panel()
        splitter.addWidget(self.vision_panel)
        
        # Set splitter sizes
        splitter.setSizes([420, 700, 280])
        
        # Status bar
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
        
        # Header
        header = QLabel("💬 对话")
        header.setObjectName("header")
        layout.addWidget(header)
        
        # Chat history
        self.chat_history = QTextEdit()
        self.chat_history.setObjectName("chat_history")
        self.chat_history.setReadOnly(True)
        layout.addWidget(self.chat_history)
        
        # Input area
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
        
        # Quick actions
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
        """Create canvas panel (execution blueprint)"""
        panel = QWidget()
        panel.setObjectName("canvas_panel")
        panel.setMinimumWidth(400)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header_layout = QHBoxLayout()
        
        header = QLabel("📋 执行蓝图")
        header.setObjectName("header")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        # Pause/Resume button
        self.pause_btn = QPushButton("⏸️ 暂停")
        self.pause_btn.setObjectName("action_btn")
        self.pause_btn.clicked.connect(self.on_pause)
        header_layout.addWidget(self.pause_btn)
        
        # Replan button
        replan_btn = QPushButton("🔄 重新规划")
        replan_btn.setObjectName("action_btn")
        replan_btn.clicked.connect(self.on_replan)
        header_layout.addWidget(replan_btn)
        
        layout.addLayout(header_layout)
        
        # Canvas scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.canvas_content = QWidget()
        self.canvas_layout = QVBoxLayout(self.canvas_content)
        self.canvas_layout.setAlignment(Qt.AlignTop)
        self.canvas_layout.setSpacing(10)
        self.canvas_layout.setContentsMargins(15, 15, 15, 15)
        
        # Placeholder
        self.canvas_placeholder = QLabel(
            "执行蓝图将在这里显示\n\n"
            "开始一个任务来查看执行流程"
        )
        self.canvas_placeholder.setAlignment(Qt.AlignCenter)
        self.canvas_placeholder.setStyleSheet(
            "color: #999; font-size: 14px; padding: 50px;"
        )
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
        
        # Header
        header = QLabel("📜 日志")
        header.setObjectName("header")
        layout.addWidget(header)
        
        # Log viewer
        self.log_viewer = QTextEdit()
        self.log_viewer.setObjectName("log_viewer")
        self.log_viewer.setReadOnly(True)
        layout.addWidget(self.log_viewer)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        return panel
    
    def _add_welcome_message(self):
        """Add welcome message"""
        welcome = """
        <h2>🤖 Blueclaw v1.0</h2>
        <p>AI Self-Operating Canvas Framework</p>
        <hr>
        <p><b>我可以帮你：</b></p>
        <ul>
            <li>✈️ 规划旅行行程</li>
            <li>📁 执行文件操作</li>
            <li>🐍 编写Python代码</li>
            <li>🔍 搜索网络信息</li>
        </ul>
        <p>请输入你想做什么...</p>
        """
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
            self,
            "重新规划",
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
    
    # ==================== Callback Handlers ====================
    
    def on_state_change(self, state):
        """Handle state change"""
        self.status_bar.showMessage(
            f"状态: {state.phase} | 进度: {state.progress}% | 模式: {state.execution_mode}"
        )
        self.progress_bar.setValue(state.progress)
    
    def on_message(self, msg: str):
        """Handle log message"""
        self.log_message(msg)
    
    def log_message(self, msg: str):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_viewer.append(f"[{timestamp}] {msg}")
        # Auto scroll
        scrollbar = self.log_viewer.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_execution_preview(self, preview: Dict):
        """Handle execution preview"""
        steps = preview.get('steps', [])
        text = f"<b>📋 执行计划 ({len(steps)} 个步骤)</b><br>"
        for i, step in enumerate(steps):
            text += f"{i+1}. {step.get('name', '未命名')}<br>"
        self.add_chat_message("ai", text)
    
    def on_question(self, question):
        """Handle clarification question"""
        def show_dialog():
            dialog = QuestionDialog(question, self)
            dialog.answered.connect(
                lambda ans: self.on_question_answered(ans, question)
            )
            dialog.exec_()
        
        # Show on main thread
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, show_dialog)
    
    def on_question_answered(self, answer: str, question):
        """Handle question answer"""
        self.add_chat_message("user", f"[{question.id}] {answer}")
        
        thread = threading.Thread(
            target=lambda: asyncio.run(
                self.coordinator.handle_user_response(answer, "question_answer")
            ),
            daemon=True
        )
        thread.start()
    
    def on_options(self, options):
        """Handle options"""
        def show_dialog():
            dialog = OptionsDialog("选择执行方案", options, self)
            dialog.selected.connect(self.on_option_selected)
            dialog.exec_()
        
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, show_dialog)
    
    def on_option_selected(self, option_id: str):
        """Handle option selection"""
        self.add_chat_message("user", f"选择: [{option_id}]")
        
        thread = threading.Thread(
            target=lambda: asyncio.run(
                self.coordinator.handle_user_response(option_id, "option_selection")
            ),
            daemon=True
        )
        thread.start()
    
    def on_blueprint_loaded(self, steps):
        """Handle blueprint loaded"""
        self.clear_canvas()
        
        for i, step in enumerate(steps):
            widget = StepWidget(
                index=i,
                name=step.name,
                description=step.description
            )
            self.step_widgets[widget.step_id] = widget
            self.canvas_layout.addWidget(widget)
    
    def on_step_update(self, step_id: str, status: str, index: int):
        """Handle step update"""
        if step_id in self.step_widgets:
            self.step_widgets[step_id].set_status(status)
        elif f"step_{index}" in self.step_widgets:
            self.step_widgets[f"step_{index}"].set_status(status)
    
    def on_execution_complete(self, result: Dict):
        """Handle execution complete"""
        success = result.get('success', False)
        summary = result.get('summary', '执行完成')
        
        icon = "✅" if success else "❌"
        self.add_chat_message("ai", f"<h3>{icon} {summary}</h3>")
        
        QMessageBox.information(self, "执行完成", summary)
    
    def on_intervention_needed(self, step_id: str, reason: str):
        """Handle intervention needed"""
        reply = QMessageBox.question(
            self,
            "需要干预",
            f"步骤需要干预: {reason}\n\n是否回退到思考阶段重新规划？",
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
        # Auto scroll
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_canvas(self):
        """Clear canvas"""
        # Remove all step widgets
        for widget in self.step_widgets.values():
            widget.deleteLater()
        self.step_widgets.clear()
        
        # Show placeholder
        self.canvas_placeholder.show()


def main():
    """Main entry"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application font
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    window = BlueclawMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
