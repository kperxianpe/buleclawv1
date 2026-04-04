#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
blueclaw_v1_gui_with_thinking.py - Blueclaw v1.0 with Thinking Blueprint Integration

集成四选项交互模式的GUI版本
Layout:
- Left (30%): Chat Panel
- Center (50%): Canvas with Thinking Blueprint + Execution Blueprint
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
        QToolButton, QMenu, QAction, QSystemTrayIcon, QStyle, QSizePolicy
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
    from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QTextCursor
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("PyQt5 not available. Install: pip install PyQt5")
    sys.exit(1)

# Import Thinking Blueprint
from core.thinking_engine import ThinkingEngine, IntentType
from core.thinking_widgets import ThinkingBlueprintWidget

from blueclaw import create_coordinator_v3


# ==================== Styles ====================

STYLESHEET = """
QMainWindow {
    background-color: #1e1e1e;
}

QWidget#chat_panel {
    background-color: #252526;
    border-right: 1px solid #3d3d3d;
}

QWidget#canvas_panel {
    background-color: #1e1e1e;
}

QWidget#vision_panel {
    background-color: #252526;
    border-left: 1px solid #3d3d3d;
}

QTextEdit#chat_history {
    background-color: #252526;
    color: #d4d4d4;
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
    border: 2px solid #3d3d3d;
    border-radius: 20px;
    padding: 8px 15px;
    font-size: 13px;
    background-color: #3c3c3c;
    color: #d4d4d4;
}

QLineEdit#input_field:focus {
    border-color: #0e639c;
    background-color: #3c3c3c;
}

QPushButton#send_btn {
    background-color: #0e639c;
    color: white;
    border: none;
    border-radius: 20px;
    padding: 8px 20px;
    font-weight: bold;
}

QPushButton#send_btn:hover {
    background-color: #1177bb;
}

QPushButton#send_btn:pressed {
    background-color: #094771;
}

QPushButton#action_btn {
    background-color: #3c3c3c;
    border: 1px solid #5a5a5a;
    border-radius: 15px;
    padding: 5px 15px;
    font-size: 12px;
    color: #d4d4d4;
}

QPushButton#action_btn:hover {
    background-color: #4d4d4d;
}

QLabel#step_title {
    font-weight: bold;
    font-size: 13px;
    color: #d4d4d4;
}

QLabel#step_desc {
    font-size: 11px;
    color: #a0a0a0;
}

QFrame#step_frame {
    background-color: #2d2d2d;
    border: 2px solid #3d3d3d;
    border-radius: 8px;
}

QFrame#step_frame[status="running"] {
    border-color: #2196f3;
    background-color: #1a2f3f;
}

QFrame#step_frame[status="completed"] {
    border-color: #4caf50;
    background-color: #1a3a1a;
}

QFrame#step_frame[status="failed"] {
    border-color: #f44336;
    background-color: #3a1a1a;
}

QFrame#step_frame[status="paused"] {
    border-color: #ff9800;
    background-color: #3a2a1a;
}

QLabel#header {
    font-size: 14px;
    font-weight: bold;
    color: #d4d4d4;
    padding: 10px;
}

QTabWidget::pane {
    border: none;
    background-color: #1e1e1e;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #a0a0a0;
    padding: 8px 16px;
    border: none;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border-bottom: 2px solid #0e639c;
}

QTabBar::tab:hover {
    background-color: #3d3d3d;
    color: #d4d4d4;
}
"""


# ==================== Execution Step Widget ====================

class ExecutionStepWidget(QFrame):
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
        
        # Status icon (using ASCII instead of emoji)
        self.icon_label = QLabel("[ ]")
        self.icon_label.setStyleSheet("font-size: 16px; color: #888;")
        layout.addWidget(self.icon_label)
        
        # Content
        content = QVBoxLayout()
        content.setSpacing(3)
        
        self.title_label = QLabel(f"Step {self.index + 1}: {self.name}")
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
        self.result_label.setStyleSheet("color: #888; font-size: 11px;")
        self.result_label.hide()
        content.addWidget(self.result_label)
    
    def set_status(self, status: str, result: str = None):
        """Update step status"""
        self.status = status
        self.setProperty("status", status)
        self.style().unpolish(self)
        self.style().polish(self)
        
        icons = {
            "pending": "[ ]",
            "running": "[~]",
            "completed": "[+]",
            "failed": "[x]",
            "paused": "[=]",
            "skipped": "[>]"
        }
        colors = {
            "pending": "#888",
            "running": "#2196f3",
            "completed": "#4caf50",
            "failed": "#f44336",
            "paused": "#ff9800",
            "skipped": "#888"
        }
        icon = icons.get(status, "[?]")
        color = colors.get(status, "#888")
        self.icon_label.setText(icon)
        self.icon_label.setStyleSheet(f"font-size: 16px; color: {color};")
        
        if result:
            self.result_label.setText(result)
            self.result_label.show()


# ==================== Main Window ====================

class BlueclawMainWindow(QMainWindow):
    """Blueclaw v1.0 Main Window with Thinking Blueprint"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Blueclaw v1.0 - AI Self-Operating Canvas (with Thinking Blueprint)")
        self.setGeometry(100, 100, 1600, 900)
        
        # Initialize systems
        self.coordinator = create_coordinator_v3(use_real_execution=True)
        self.setup_callbacks()
        
        # Step widgets storage
        self.step_widgets: Dict[str, ExecutionStepWidget] = {}
        
        # Current thinking result
        self.current_thinking_result = None
        
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
        
        # === Left Panel: Chat (25%) ===
        self.chat_panel = self._create_chat_panel()
        splitter.addWidget(self.chat_panel)
        
        # === Center Panel: Canvas with Thinking Blueprint (55%) ===
        self.canvas_panel = self._create_canvas_panel()
        splitter.addWidget(self.canvas_panel)
        
        # === Right Panel: Vision/Log (20%) ===
        self.vision_panel = self._create_vision_panel()
        splitter.addWidget(self.vision_panel)
        
        # Set splitter sizes
        splitter.setSizes([400, 880, 320])
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready | Mode: Thinking Blueprint + Real Execution")
    
    def _create_chat_panel(self) -> QWidget:
        """Create chat panel"""
        panel = QWidget()
        panel.setObjectName("chat_panel")
        panel.setMinimumWidth(300)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QLabel("Chat")
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
        self.input_field.setPlaceholderText("Enter your task...")
        self.input_field.returnPressed.connect(self.on_send)
        input_layout.addWidget(self.input_field)
        
        send_btn = QPushButton("Send")
        send_btn.setObjectName("send_btn")
        send_btn.clicked.connect(self.on_send)
        input_layout.addWidget(send_btn)
        
        layout.addWidget(input_frame)
        
        # Quick actions
        quick_frame = QFrame()
        quick_layout = QHBoxLayout(quick_frame)
        quick_layout.setContentsMargins(10, 0, 10, 10)
        
        quick_tasks = [
            ("Plan Travel", "I want to plan a weekend trip"),
            ("List Files", "List files in current directory"),
            ("Write Code", "Write a Python script to batch rename files"),
        ]
        
        for label, task in quick_tasks:
            btn = QPushButton(label)
            btn.setObjectName("action_btn")
            btn.clicked.connect(lambda checked, t=task: self.quick_task(t))
            quick_layout.addWidget(btn)
        
        layout.addWidget(quick_frame)
        
        return panel
    
    def _create_canvas_panel(self) -> QWidget:
        """Create canvas panel with stacked widget for Thinking + Execution"""
        panel = QWidget()
        panel.setObjectName("canvas_panel")
        panel.setMinimumWidth(500)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.canvas_header = QLabel("Thinking Blueprint")
        self.canvas_header.setObjectName("header")
        header_layout.addWidget(self.canvas_header)
        
        header_layout.addStretch()
        
        # Switch button
        self.switch_btn = QPushButton("View Execution")
        self.switch_btn.setObjectName("action_btn")
        self.switch_btn.clicked.connect(self.on_switch_view)
        self.switch_btn.setEnabled(False)
        header_layout.addWidget(self.switch_btn)
        
        # Pause/Resume button
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setObjectName("action_btn")
        self.pause_btn.clicked.connect(self.on_pause)
        self.pause_btn.setEnabled(False)
        header_layout.addWidget(self.pause_btn)
        
        layout.addLayout(header_layout)
        
        # Stacked widget for switching between Thinking and Execution
        self.canvas_stack = QStackedWidget()
        
        # Page 1: Thinking Blueprint
        self.thinking_widget = ThinkingBlueprintWidget()
        self.thinking_widget.option_selected.connect(self.on_thinking_option_selected)
        self.thinking_widget.execute_clicked.connect(self.on_thinking_execute)
        self.thinking_widget.cancel_clicked.connect(self.on_thinking_cancel)
        self.canvas_stack.addWidget(self.thinking_widget)
        
        # Page 2: Execution Blueprint
        self.execution_widget = QWidget()
        execution_layout = QVBoxLayout(self.execution_widget)
        execution_layout.setContentsMargins(0, 0, 0, 0)
        
        # Execution scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.execution_content = QWidget()
        self.execution_layout = QVBoxLayout(self.execution_content)
        self.execution_layout.setAlignment(Qt.AlignTop)
        self.execution_layout.setSpacing(10)
        self.execution_layout.setContentsMargins(15, 15, 15, 15)
        
        # Placeholder
        self.execution_placeholder = QLabel(
            "Execution Blueprint will appear here\n\n"
            "Start a task to view execution flow"
        )
        self.execution_placeholder.setAlignment(Qt.AlignCenter)
        self.execution_placeholder.setStyleSheet(
            "color: #888; font-size: 14px; padding: 50px;"
        )
        self.execution_layout.addWidget(self.execution_placeholder)
        
        scroll.setWidget(self.execution_content)
        execution_layout.addWidget(scroll)
        
        self.canvas_stack.addWidget(self.execution_widget)
        
        layout.addWidget(self.canvas_stack)
        
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
        header = QLabel("Log")
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
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #3d3d3d;
                text-align: center;
                color: #d4d4d4;
            }
            QProgressBar::chunk {
                background-color: #0e639c;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        return panel
    
    def _add_welcome_message(self):
        """Add welcome message"""
        welcome = """
        <h2>Blueclaw v1.0 with Thinking Blueprint</h2>
        <p>AI Self-Operating Canvas Framework with 4-Option Interactive Mode</p>
        <hr>
        <p><b>I can help you:</b></p>
        <ul>
            <li>Plan travel itineraries</li>
            <li>Execute file operations</li>
            <li>Write Python code</li>
            <li>Search web information</li>
        </ul>
        <p>Enter what you want to do...</p>
        """
        self.add_chat_message("ai", welcome)
    
    # ==================== Event Handlers ====================
    
    def on_send(self):
        """Handle send button - Show Thinking Blueprint first"""
        text = self.input_field.text().strip()
        if not text:
            return
        
        self.input_field.clear()
        self.add_chat_message("user", text)
        
        # Show thinking blueprint with 4 options
        self.canvas_header.setText("Thinking Blueprint")
        self.canvas_stack.setCurrentIndex(0)  # Show thinking page
        self.switch_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        
        # Analyze input with thinking engine
        self.thinking_widget.analyze_input(text)
        self.log_message(f"Thinking Blueprint analyzing: {text[:50]}...")
    
    def on_thinking_option_selected(self, option_id, thinking_result):
        """Handle option selection in thinking blueprint"""
        option = thinking_result.get_option(option_id)
        if option:
            self.log_message(f"Selected option [{option.label}]: {option.title}")
    
    def on_thinking_execute(self, option_id, thinking_result):
        """Handle execute button in thinking blueprint"""
        option = thinking_result.get_option(option_id)
        if not option:
            return
        
        # Get execution result
        exec_result = self.thinking_widget.get_execution_result()
        
        # Switch to execution view
        self.canvas_stack.setCurrentIndex(1)  # Show execution page
        self.canvas_header.setText("Execution Blueprint")
        self.switch_btn.setText("View Thinking")
        self.switch_btn.setEnabled(True)
        self.pause_btn.setEnabled(True)
        
        # Add message to chat
        self.add_chat_message("ai", f"<b>Executing:</b> {option.title}<br>{option.description}")
        
        # Start actual execution
        original_input = thinking_result.context.get("original_input", "")
        thread = threading.Thread(
            target=lambda: asyncio.run(self.coordinator.start_task(original_input)),
            daemon=True
        )
        thread.start()
        
        self.log_message(f"Started execution with action: {exec_result['action']}")
    
    def on_thinking_cancel(self):
        """Handle cancel button in thinking blueprint"""
        self.log_message("User cancelled thinking blueprint")
        self.add_chat_message("ai", "Task cancelled. Enter a new task when ready.")
    
    def on_switch_view(self):
        """Switch between thinking and execution views"""
        current = self.canvas_stack.currentIndex()
        new_index = 1 - current  # Toggle between 0 and 1
        self.canvas_stack.setCurrentIndex(new_index)
        
        if new_index == 0:
            self.canvas_header.setText("Thinking Blueprint")
            self.switch_btn.setText("View Execution")
        else:
            self.canvas_header.setText("Execution Blueprint")
            self.switch_btn.setText("View Thinking")
    
    def quick_task(self, task: str):
        """Quick task button"""
        self.input_field.setText(task)
        self.on_send()
    
    def on_pause(self):
        """Pause/Resume execution"""
        if self.coordinator.execution_system.is_paused:
            self.coordinator.execution_system.resume_execution()
            self.pause_btn.setText("Pause")
        else:
            self.coordinator.execution_system.pause_execution()
            self.pause_btn.setText("Resume")
    
    # ==================== Callback Handlers ====================
    
    def on_state_change(self, state):
        """Handle state change"""
        self.status_bar.showMessage(
            f"State: {state.phase} | Progress: {state.progress}% | Mode: {state.execution_mode}"
        )
        self.progress_bar.setValue(state.progress)
    
    def on_message(self, msg: str):
        """Handle log message"""
        self.log_message(msg)
    
    def log_message(self, msg: str):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_viewer.append(f"[{timestamp}] {msg}")
        scrollbar = self.log_viewer.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def add_chat_message(self, sender: str, message: str):
        """Add message to chat"""
        timestamp = datetime.now().strftime("%H:%M")
        
        if sender == "user":
            html = f"""
            <div style="margin: 10px 0; text-align: right;">
                <span style="background-color: #0e639c; color: white; 
                    padding: 8px 12px; border-radius: 15px; display: inline-block; 
                    max-width: 80%; text-align: left;">
                    {message}
                </span>
                <div style="font-size: 10px; color: #888; margin-top: 4px;">{timestamp}</div>
            </div>
            """
        else:
            html = f"""
            <div style="margin: 10px 0;">
                <span style="background-color: #3c3c3c; color: #d4d4d4; 
                    padding: 8px 12px; border-radius: 15px; display: inline-block; 
                    max-width: 80%;">
                    {message}
                </span>
                <div style="font-size: 10px; color: #888; margin-top: 4px;">{timestamp}</div>
            </div>
            """
        
        self.chat_history.insertHtml(html)
        self.chat_history.insertHtml("<br>")
        
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_history.setTextCursor(cursor)
    
    def on_execution_preview(self, preview: Dict):
        """Handle execution preview"""
        steps = preview.get('steps', [])
        text = f"<b>Execution Plan ({len(steps)} steps)</b><br>"
        for i, step in enumerate(steps):
            text += f"{i+1}. {step.get('name', 'Unnamed')}<br>"
        self.add_chat_message("ai", text)
    
    def on_question(self, question):
        """Handle clarification question"""
        def show_dialog():
            from PyQt5.QtWidgets import QInputDialog
            answer, ok = QInputDialog.getText(
                self, "Clarification Needed", question.text
            )
            if ok and answer:
                self.on_question_answered(answer, question)
        
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
        """Handle options (from coordinator)"""
        # This is handled by thinking blueprint now
        pass
    
    def on_option_selected(self, option_id: str):
        """Handle option selection (from coordinator)"""
        self.add_chat_message("user", f"Selected: [{option_id}]")
        
        thread = threading.Thread(
            target=lambda: asyncio.run(
                self.coordinator.handle_user_response(option_id, "option_selection")
            ),
            daemon=True
        )
        thread.start()
    
    def on_blueprint_loaded(self, steps):
        """Handle blueprint loaded"""
        self.clear_execution_canvas()
        
        for i, step in enumerate(steps):
            widget = ExecutionStepWidget(
                index=i,
                name=step.name,
                description=step.description
            )
            self.step_widgets[widget.step_id] = widget
            self.execution_layout.addWidget(widget)
    
    def clear_execution_canvas(self):
        """Clear execution canvas"""
        # Remove existing step widgets
        for widget in self.step_widgets.values():
            widget.deleteLater()
        self.step_widgets.clear()
        
        # Hide placeholder
        if hasattr(self, 'execution_placeholder'):
            self.execution_placeholder.hide()
    
    def on_step_update(self, step_id: str, status: str, index: int):
        """Handle step update"""
        if step_id in self.step_widgets:
            self.step_widgets[step_id].set_status(status)
        elif f"step_{index}" in self.step_widgets:
            self.step_widgets[f"step_{index}"].set_status(status)
    
    def on_execution_complete(self, result: Dict):
        """Handle execution complete"""
        success = result.get('success', False)
        summary = result.get('summary', 'Execution completed')
        
        icon = "[+]" if success else "[x]"
        self.add_chat_message("ai", f"<h3>{icon} {summary}</h3>")
        
        self.pause_btn.setEnabled(False)
        QMessageBox.information(self, "Execution Complete", summary)
    
    def on_intervention_needed(self, step_id: str, reason: str):
        """Handle intervention needed"""
        reply = QMessageBox.question(
            self,
            "Intervention Needed",
            f"Step needs intervention: {reason}\n\nRevert to thinking phase to replan?",
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


# ==================== Main Entry ====================

def main():
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
