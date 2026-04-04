#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chat_panel.py - Blueclaw v1.0 Chat Panel

对话面板 - 支持嵌入思考画布小画布
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QScrollArea, QFrame, QLabel, QSizePolicy,
    QGraphicsView
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCursor
from datetime import datetime
from typing import Optional


class ChatMessageWidget(QWidget):
    """单条消息组件"""
    
    def __init__(self, sender: str, message: str, parent=None):
        super().__init__(parent)
        
        self.sender = sender
        self.message = message
        self.timestamp = datetime.now().strftime("%H:%M")
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(2)
        
        # 根据发送者设置样式
        if self.sender == "user":
            # 用户消息 - 右侧
            alignment = Qt.AlignRight
            bubble_style = """
                background-color: #0e639c;
                color: white;
                padding: 10px 15px;
                border-radius: 15px;
            """
        else:
            # AI 消息 - 左侧
            alignment = Qt.AlignLeft
            bubble_style = """
                background-color: #3c3c3c;
                color: #d4d4d4;
                padding: 10px 15px;
                border-radius: 15px;
            """
            
        # 消息气泡
        self.message_label = QLabel(self.message)
        self.message_label.setStyleSheet(bubble_style)
        self.message_label.setWordWrap(True)
        self.message_label.setMaximumWidth(500)
        self.message_label.setFont(QFont("Microsoft YaHei", 10))
        
        # 时间戳
        self.time_label = QLabel(self.timestamp)
        self.time_label.setStyleSheet("color: #888; font-size: 9px;")
        
        # 布局
        h_layout = QHBoxLayout()
        if self.sender == "user":
            h_layout.addStretch()
            h_layout.addWidget(self.message_label)
        else:
            h_layout.addWidget(self.message_label)
            h_layout.addStretch()
            
        layout.addLayout(h_layout)
        
        time_layout = QHBoxLayout()
        if self.sender == "user":
            time_layout.addStretch()
            time_layout.addWidget(self.time_label)
        else:
            time_layout.addWidget(self.time_label)
            time_layout.addStretch()
            
        layout.addLayout(time_layout)


class ChatPanel(QWidget):
    """
    对话面板 - 支持嵌入思考画布
    
    特点：
    - 滚动消息列表
    - 支持嵌入 QWidget（思考画布）
    - 输入框和发送按钮
    """
    
    message_sent = pyqtSignal(str)  # 用户发送的消息
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._setup_ui()
        self._setup_styles()
        
    def _setup_ui(self):
        """设置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题栏
        self.header = QLabel("Chat")
        self.header.setStyleSheet("""
            background-color: #252526;
            color: #d4d4d4;
            padding: 10px 15px;
            font-size: 14px;
            font-weight: bold;
            border-bottom: 1px solid #3d3d3d;
        """)
        layout.addWidget(self.header)
        
        # 消息区域（滚动）
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background-color: #1e1e1e; border: none;")
        
        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setSpacing(5)
        self.messages_layout.setContentsMargins(5, 10, 5, 10)
        
        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area, stretch=1)
        
        # 嵌入画布区域（动态显示）
        self.embedded_canvas_container = QWidget()
        self.embedded_canvas_layout = QVBoxLayout(self.embedded_canvas_container)
        self.embedded_canvas_layout.setContentsMargins(10, 5, 10, 5)
        self.embedded_canvas_container.hide()
        layout.addWidget(self.embedded_canvas_container)
        
        # 输入区域
        input_frame = QFrame()
        input_frame.setStyleSheet("background-color: #252526; border-top: 1px solid #3d3d3d;")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        # 输入框
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Enter your task...")
        self.input_field.setFont(QFont("Microsoft YaHei", 11))
        self.input_field.returnPressed.connect(self._on_send)
        input_layout.addWidget(self.input_field)
        
        # 发送按钮
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self.send_btn)
        
        layout.addWidget(input_frame)
        
        # 快捷任务按钮
        quick_frame = QFrame()
        quick_frame.setStyleSheet("background-color: #252526;")
        quick_layout = QHBoxLayout(quick_frame)
        quick_layout.setContentsMargins(10, 0, 10, 10)
        
        quick_tasks = [
            ("Plan Travel", "I want to plan a weekend trip"),
            ("List Files", "List files in current directory"),
            ("Write Code", "Write a Python script"),
        ]
        
        for label, task in quick_tasks:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3c3c3c;
                    color: #d4d4d4;
                    border: 1px solid #5a5a5a;
                    border-radius: 12px;
                    padding: 4px 12px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #4d4d4d;
                }
            """)
            btn.clicked.connect(lambda checked, t=task: self._on_quick_task(t))
            quick_layout.addWidget(btn)
            
        quick_layout.addStretch()
        layout.addWidget(quick_frame)
        
    def _setup_styles(self):
        """设置样式"""
        self.setStyleSheet("""
            ChatPanel {
                background-color: #1e1e1e;
            }
            QLineEdit {
                background-color: #3c3c3c;
                color: #d4d4d4;
                border: 1px solid #5a5a5a;
                border-radius: 18px;
                padding: 8px 15px;
            }
            QLineEdit:focus {
                border-color: #0e639c;
            }
            QPushButton#send_btn {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 18px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton#send_btn:hover {
                background-color: #1177bb;
            }
        """)
        
    def add_message(self, sender: str, message: str):
        """
        添加消息
        
        Args:
            sender: "user" 或 "ai"
            message: 消息内容
        """
        msg_widget = ChatMessageWidget(sender, message)
        self.messages_layout.addWidget(msg_widget)
        
        # 滚动到底部
        QTimer.singleShot(100, self._scroll_to_bottom)
        
    def _scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def append_thinking_canvas(self, canvas_widget: QWidget):
        """
        嵌入思考画布
        
        Args:
            canvas_widget: 思考画布控件
        """
        # 清空旧画布
        self.clear_embedded_canvas()
        
        # 添加新画布
        self.embedded_canvas_layout.addWidget(canvas_widget)
        self.embedded_canvas_container.show()
        
        # 添加提示文字
        label = QLabel("Thinking... Please select an option:")
        label.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")
        self.embedded_canvas_layout.insertWidget(0, label)
        
        # 滚动到底部显示画布
        QTimer.singleShot(200, self._scroll_to_bottom)
        
    def clear_embedded_canvas(self):
        """清除嵌入的画布"""
        while self.embedded_canvas_layout.count():
            item = self.embedded_canvas_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.embedded_canvas_container.hide()
        
    def clear_messages(self):
        """清空所有消息"""
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
    def _on_send(self):
        """发送按钮点击"""
        text = self.input_field.text().strip()
        if text:
            self.add_message("user", text)
            self.input_field.clear()
            self.message_sent.emit(text)
            
    def _on_quick_task(self, task: str):
        """快捷任务点击"""
        self.input_field.setText(task)
        self._on_send()
        
    def set_input_enabled(self, enabled: bool):
        """设置输入框状态"""
        self.input_field.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        
    def add_system_message(self, message: str):
        """添加系统消息"""
        self.add_message("ai", f"<i>{message}</i>")
