#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
blueclaw_v1_gui_thinking.py - Blueclaw v1.0 + Thinking Blueprint

新增功能：
1. 意图识别显示
2. 思考过程可视化
3. 四选一选项交互
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
from blueclaw.core.thinking_options import (
    ThinkingBlueprintEngine, ThinkingBlueprintResult, IntentType
)


# ==================== Styles ====================

STYLESHEET = """
QMainWindow {
    background-color: #f5f5f5;
}

QWidget#chat_panel {
    background-color: #ffffff;
    border-right: 1px solid #e0e0e0;
}

QWidget#thinking_panel {
    background-color: #fafafa;
    border-right: 1px solid #e0e0e0;
}

QWidget#canvas_panel {
    background-color: #ffffff;
}

QTextEdit#chat_history {
    background-color: #ffffff;
    border: none;
    font-family: "Microsoft YaHei", sans-serif;
    font-size: 13px;
    line-height: 1.5;
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

QPushButton#option_btn {
    background-color: #ffffff;
    border: 2px solid #e0e0e0;
    border-radius: 10px;
    padding: 15px;
    font-size: 13px;
    text-align: left;
}

QPushButton#option_btn:hover {
    border-color: #2196f3;
    background-color: #e3f2fd;
}

QPushButton#option_btn:disabled {
    background-color: #e8f5e9;
    border-color: #4caf50;
}

QFrame#thinking_step {
    background-color: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 10px;
}

QFrame#intent_frame {
    background-color: #e3f2fd;
    border: 1px solid #bbdefb;
    border-radius: 8px;
    padding: 10px;
}

QLabel#header {
    font-size: 14px;
    font-weight: bold;
    color: #333;
    padding: 10px;
}

QLabel#intent_label {
    font-size: 12px;
    color: #1976d2;
    font-weight: bold;
}
"""


# ==================== Thinking Option Button ====================

class OptionButton(QPushButton):
    """选项按钮"""
    
    clicked_with_id = pyqtSignal(str)
    
    def __init__(self, option_id: str, icon: str, title: str, description: str, confidence: int, parent=None):
        super().__init__(parent)
        self.option_id = option_id
        
        self.setObjectName("option_btn")
        self.setMinimumHeight(80)
        self.setCursor(Qt.PointingHandCursor)
        
        # Build text
        confidence_bar = "█" * int(confidence / 10) + "░" * (10 - int(confidence / 10))
        text = f"<b>[{option_id}] {icon} {title}</b><br>"
        text += f"<span style='color: #666; font-size: 11px;'>{description}</span><br>"
        text += f"<span style='color: #999; font-size: 10px;'>匹配度: {confidence_bar} {confidence}%</span>"
        
        self.setText(text)
        self.clicked.connect(lambda: self.clicked_with_id.emit(option_id))


# ==================== Main Window ====================

class BlueclawThinkingGUI(QMainWindow):
    """Blueclaw v1.0 with Thinking Blueprint"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blueclaw v1.0 - Thinking Blueprint")
        self.setMinimumSize(1400, 800)
        
        # Initialize systems
        self.coordinator = create_coordinator_v3()
        self.thinking_engine = ThinkingBlueprintEngine()
        self.current_blueprint = None
        
        # Set up callbacks
        self.coordinator.set_callbacks(
            on_state_change=self.on_state_change,
            on_message=self.on_message
        )
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up UI"""
        self.setStyleSheet(STYLESHEET)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # === Left Panel: Chat (25%) ===
        self.chat_panel = self._create_chat_panel()
        splitter.addWidget(self.chat_panel)
        
        # === Center Panel: Thinking Blueprint (35%) ===
        self.thinking_panel = self._create_thinking_panel()
        splitter.addWidget(self.thinking_panel)
        
        # === Right Panel: Canvas Execution (40%) ===
        self.canvas_panel = self._create_canvas_panel()
        splitter.addWidget(self.canvas_panel)
        
        # Set splitter sizes
        splitter.setSizes([350, 490, 560])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("就绪 | 模式: Thinking Blueprint")
    
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
        
        return panel
    
    def _create_thinking_panel(self) -> QWidget:
        """Create thinking blueprint panel (NEW)"""
        panel = QWidget()
        panel.setObjectName("thinking_panel")
        panel.setMinimumWidth(350)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 0, 10, 10)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("🧠 思考蓝图")
        header.setObjectName("header")
        layout.addWidget(header)
        
        # Scroll area for thinking content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.thinking_content = QWidget()
        self.thinking_layout = QVBoxLayout(self.thinking_content)
        self.thinking_layout.setAlignment(Qt.AlignTop)
        self.thinking_layout.setSpacing(15)
        
        # Placeholder
        self.thinking_placeholder = QLabel(
            "思考蓝图将在这里显示\n\n"
            "开始一个任务来查看意图识别和选项"
        )
        self.thinking_placeholder.setAlignment(Qt.AlignCenter)
        self.thinking_placeholder.setStyleSheet(
            "color: #999; font-size: 13px; padding: 30px;"
        )
        self.thinking_layout.addWidget(self.thinking_placeholder)
        
        scroll.setWidget(self.thinking_content)
        layout.addWidget(scroll)
        
        return panel
    
    def _create_canvas_panel(self) -> QWidget:
        """Create canvas panel"""
        panel = QWidget()
        panel.setObjectName("canvas_panel")
        panel.setMinimumWidth(400)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QLabel("📋 执行蓝图")
        header.setObjectName("header")
        layout.addWidget(header)
        
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
            "执行步骤将在这里显示"
        )
        self.canvas_placeholder.setAlignment(Qt.AlignCenter)
        self.canvas_placeholder.setStyleSheet(
            "color: #999; font-size: 14px; padding: 50px;"
        )
        self.canvas_layout.addWidget(self.canvas_placeholder)
        
        scroll.setWidget(self.canvas_content)
        layout.addWidget(scroll)
        
        return panel
    
    def on_send(self):
        """Handle send button - NEW with Thinking Blueprint"""
        text = self.input_field.text().strip()
        if not text:
            return
        
        self.input_field.clear()
        self.add_chat_message("user", text)
        
        # Step 1: Analyze with Thinking Engine
        self.show_thinking_analysis(text)
    
    def show_thinking_analysis(self, user_input: str):
        """Show thinking analysis and options"""
        # Analyze
        self.current_blueprint = self.thinking_engine.analyze(user_input)
        
        # Clear thinking panel
        while self.thinking_layout.count():
            item = self.thinking_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 1. Intent Recognition
        intent_frame = QFrame()
        intent_frame.setObjectName("intent_frame")
        intent_layout = QVBoxLayout(intent_frame)
        intent_layout.setContentsMargins(12, 10, 12, 10)
        
        intent_title = QLabel("🎯 意图识别")
        intent_title.setStyleSheet("font-weight: bold; color: #1565c0;")
        intent_layout.addWidget(intent_title)
        
        intent_text = QLabel(
            f"意图: <b>{self.current_blueprint.intent.value.upper()}</b><br>"
            f"置信度: {self.current_blueprint.intent_confidence:.0%}"
        )
        intent_text.setStyleSheet("color: #333; font-size: 12px;")
        intent_layout.addWidget(intent_text)
        
        self.thinking_layout.addWidget(intent_frame)
        
        # 2. Thinking Steps
        steps_title = QLabel("🧠 思考过程")
        steps_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.thinking_layout.addWidget(steps_title)
        
        for step in self.current_blueprint.thinking_steps:
            step_frame = QFrame()
            step_frame.setObjectName("thinking_step")
            step_layout = QVBoxLayout(step_frame)
            step_layout.setContentsMargins(10, 8, 10, 8)
            step_layout.setSpacing(3)
            
            step_header = QLabel(f"{step.icon} Step {step.step_number}: {step.title}")
            step_header.setStyleSheet("font-weight: bold; font-size: 11px;")
            step_layout.addWidget(step_header)
            
            step_content = QLabel(step.content)
            step_content.setStyleSheet("color: #666; font-size: 11px;")
            step_layout.addWidget(step_content)
            
            self.thinking_layout.addWidget(step_frame)
        
        # 3. Options Title
        options_title = QLabel("🎮 请选择一项操作")
        options_title.setStyleSheet("font-weight: bold; margin-top: 10px;")
        self.thinking_layout.addWidget(options_title)
        
        # 4. Four Options
        self.option_buttons = []
        for opt in self.current_blueprint.options:
            btn = OptionButton(
                opt.option_id,
                opt.icon,
                opt.title,
                opt.description,
                opt.confidence
            )
            btn.clicked_with_id.connect(self.on_option_selected)
            self.thinking_layout.addWidget(btn)
            self.option_buttons.append(btn)
        
        # Add stretch
        self.thinking_layout.addStretch()
        
        # Update status
        self.status_bar.showMessage(
            f"意图: {self.current_blueprint.intent.value} | "
            f"置信度: {self.current_blueprint.intent_confidence:.0%} | "
            "请选择 A/B/C/D"
        )
    
    def on_option_selected(self, option_id: str):
        """Handle option selection"""
        if not self.current_blueprint:
            return
        
        # Execute option
        result = self.thinking_engine.execute_option(self.current_blueprint, option_id)
        
        if result["success"]:
            option = result["option"]
            
            # Disable all option buttons
            for btn in self.option_buttons:
                btn.setEnabled(False)
                if btn.option_id == option_id:
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: #e8f5e9;
                            border: 3px solid #4caf50;
                            border-radius: 10px;
                            padding: 15px;
                            font-size: 13px;
                            text-align: left;
                        }
                    """)
            
            # Add to chat
            self.add_chat_message(
                "ai",
                f"✓ 选择了 [{option_id}]: {option.title}<br>"
                f"<span style='color: #666;'>正在执行: {option.action_type}</span>"
            )
            
            # Handle action
            self.handle_action(option.action_type, option.params)
        
        else:
            self.add_chat_message("ai", f"❌ 错误: {result['message']}")
    
    def handle_action(self, action_type: str, params: Dict):
        """Handle selected action"""
        # Run task in background thread
        thread = threading.Thread(
            target=lambda: asyncio.run(
                self.coordinator.start_task(self.current_blueprint.user_input)
            ),
            daemon=True
        )
        thread.start()
        
        self.status_bar.showMessage("执行中...")
    
    def add_chat_message(self, role: str, text: str):
        """Add message to chat history"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if role == "user":
            color = "#1976d2"
            prefix = "你"
        else:
            color = "#388e3c"
            prefix = "AI"
        
        html = f"""
        <div style="margin: 10px 0;">
            <span style="color: #999; font-size: 10px;">[{timestamp}]</span>
            <span style="color: {color}; font-weight: bold;">{prefix}:</span>
            <div style="margin-left: 10px; margin-top: 5px;">{text}</div>
        </div>
        """
        
        self.chat_history.append(html)
        # Auto scroll
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_state_change(self, state):
        """Handle state change"""
        self.status_bar.showMessage(
            f"状态: {state.phase} | 进度: {state.progress}%"
        )
    
    def on_message(self, msg: str):
        """Handle log message"""
        print(f"[LOG] {msg}")


def main():
    """Main entry"""
    app = QApplication(sys.argv)
    
    window = BlueclawThinkingGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
