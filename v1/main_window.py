#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main_window.py - Blueclaw v1.0 Main Window

Blueclaw v1.0 主窗口 - 整合所有组件
- 分层画布系统
- LLM 思考引擎
- 状态持久化
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QLabel, QPushButton, QStatusBar, QMessageBox,
    QAction, QMenuBar, QToolBar, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QFont, QIcon, QKeySequence

# 导入自定义组件
from v1.widgets.chat_panel import ChatPanel
from v1.canvas.layered_canvas import LayeredCanvasSystem
from v1.canvas.position_awareness import CanvasPositionAwareness, CanvasElementLocator
from v1.core.llm_thinking_engine import LLMThinkingEngine, create_llm_thinking_engine
from persistence.state_manager import StatePersistenceManager, TaskStatus

# 导入原有组件
from blueclaw import create_coordinator_v3
from core.thinking_engine import ThinkingResult, ThinkingOption


class AsyncWorker(QThread):
    """异步工作线程"""
    
    result_ready = pyqtSignal(object)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, coro):
        super().__init__()
        self.coro = coro
        
    def run(self):
        """运行异步协程"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.coro)
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class BlueclawV1MainWindow(QMainWindow):
    """
    Blueclaw v1.0 主窗口
    
    功能：
    - 左侧：对话面板（支持嵌入思考画布）
    - 右侧：执行大画布（主工作区）
    - 整合 LLM 思考引擎
    - 状态持久化
    """
    
    def __init__(self, use_llm: bool = False, llm_api_key: str = None):
        super().__init__()
        
        self.setWindowTitle("Blueclaw v1.0 - AI Self-Operating Canvas")
        self.resize(1400, 900)
        
        # 初始化核心组件
        self._init_components(use_llm, llm_api_key)
        
        # 设置 UI
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._connect_signals()
        
        # 当前任务状态
        self.current_task_id: str = ""
        self.is_processing: bool = False
        
        # 显示欢迎消息
        self._show_welcome()
        
    def _init_components(self, use_llm: bool, llm_api_key: str):
        """初始化核心组件"""
        # 协调器（原有）
        self.coordinator = create_coordinator_v3(use_real_execution=True)
        self.coordinator.set_callbacks(
            on_state_change=self._on_state_change,
            on_message=self._on_message,
            on_execution_preview=self._on_execution_preview,
            on_question=self._on_question,
            on_options=self._on_options,
            on_blueprint_loaded=self._on_blueprint_loaded,
            on_step_update=self._on_step_update,
            on_execution_complete=self._on_execution_complete,
            on_intervention_needed=self._on_intervention_needed
        )
        
        # 分层画布系统
        self.canvas_system = LayeredCanvasSystem()
        
        # 位置感知
        self.position_awareness = CanvasPositionAwareness(
            self.canvas_system.execution_canvas
        )
        self.element_locator = CanvasElementLocator(self.position_awareness)
        
        # 思考引擎（LLM 或规则）
        if use_llm:
            self.thinking_engine = create_llm_thinking_engine(
                api_key=llm_api_key,
                use_mock=(not llm_api_key)
            )
        else:
            # 使用规则引擎
            from core.thinking_engine import ThinkingEngine
            self.thinking_engine = ThinkingEngine()
            
        # 状态持久化
        self.state_manager = StatePersistenceManager()
        
    def _setup_ui(self):
        """设置 UI"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QStatusBar {
                background-color: #007acc;
                color: white;
            }
        """)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        
        # 主布局
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # 左侧：对话面板（400px 固定宽度）
        self.chat_panel = ChatPanel()
        self.chat_panel.setFixedWidth(400)
        splitter.addWidget(self.chat_panel)
        
        # 右侧：执行画布
        execution_canvas = self.canvas_system.get_execution_canvas()
        splitter.addWidget(execution_canvas)
        
        # 设置分割比例
        splitter.setSizes([400, 1000])
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态栏组件
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(150)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # 暂停按钮
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self._on_pause)
        self.status_bar.addPermanentWidget(self.pause_btn)
        
    def _setup_menu(self):
        """设置菜单"""
        menubar = self.menuBar()
        
        # File 菜单
        file_menu = menubar.addMenu("&File")
        
        new_task = QAction("&New Task", self)
        new_task.setShortcut(QKeySequence.New)
        new_task.triggered.connect(self._on_new_task)
        file_menu.addAction(new_task)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View 菜单
        view_menu = menubar.addMenu("&View")
        
        fit_view = QAction("&Fit to View", self)
        fit_view.triggered.connect(self._on_fit_view)
        view_menu.addAction(fit_view)
        
        # Tasks 菜单
        tasks_menu = menubar.addMenu("&Tasks")
        
        recent_tasks = QAction("&Recent Tasks", self)
        recent_tasks.triggered.connect(self._on_recent_tasks)
        tasks_menu.addAction(recent_tasks)
        
        recover_tasks = QAction("&Recover Tasks", self)
        recover_tasks.triggered.connect(self._on_recover_tasks)
        tasks_menu.addAction(recover_tasks)
        
    def _setup_toolbar(self):
        """设置工具栏"""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #333333;
                border-bottom: 1px solid #3d3d3d;
            }
            QToolButton {
                color: #d4d4d4;
                padding: 5px 10px;
            }
        """)
        self.addToolBar(toolbar)
        
        # 重置按钮
        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self._on_new_task)
        toolbar.addWidget(reset_btn)
        
        toolbar.addSeparator()
        
        # 缩放控制
        zoom_in = QPushButton("Zoom+")
        zoom_in.clicked.connect(lambda: self.canvas_system.execution_canvas.scale(1.2, 1.2))
        toolbar.addWidget(zoom_in)
        
        zoom_out = QPushButton("Zoom-")
        zoom_out.clicked.connect(lambda: self.canvas_system.execution_canvas.scale(0.8, 0.8))
        toolbar.addWidget(zoom_out)
        
    def _connect_signals(self):
        """连接信号"""
        # 对话面板
        self.chat_panel.message_sent.connect(self._on_user_message)
        
        # 思考画布选项选择
        thinking_canvas = self.canvas_system.get_thinking_canvas()
        thinking_canvas.option_selected.connect(self._on_thinking_option_selected)
        
        # 执行画布干预
        execution_canvas = self.canvas_system.get_execution_canvas()
        execution_canvas.node_clicked.connect(self._on_execution_node_clicked)
        execution_canvas.intervention_requested.connect(self._on_intervention_requested)
        
    def _show_welcome(self):
        """显示欢迎消息"""
        welcome_text = """<h2>Welcome to Blueclaw v1.0</h2>
<p>AI Self-Operating Canvas with Thinking Blueprint</p>
<hr>
<p><b>Features:</b></p>
<ul>
<li>Thinking Blueprint - 4-option interactive mode</li>
<li>Execution Blueprint - Visual execution flow</li>
<li>Real Skill Execution - File, Shell, Code, Search</li>
<li>State Persistence - Crash recovery</li>
</ul>
<p>Type your task below to get started...</p>"""
        
        self.chat_panel.add_message("ai", welcome_text)
        
    def _on_user_message(self, message: str):
        """用户发送消息"""
        if self.is_processing:
            return
            
        self.is_processing = True
        self.chat_panel.set_input_enabled(False)
        
        # 生成任务 ID
        self.current_task_id = self.state_manager.save_task({
            'user_input': message,
            'status': TaskStatus.THINKING.value,
            'progress': 10
        })
        
        # 更新状态
        self.status_label.setText("Thinking...")
        self.progress_bar.setValue(10)
        
        # 执行思考分析
        if isinstance(self.thinking_engine, LLMThinkingEngine):
            # LLM 引擎 - 异步
            worker = AsyncWorker(self.thinking_engine.analyze(message))
            worker.result_ready.connect(lambda result: self._on_thinking_result(result, message))
            worker.error_occurred.connect(self._on_thinking_error)
            worker.start()
        else:
            # 规则引擎 - 同步
            try:
                result = self.thinking_engine.analyze(message)
                self._on_thinking_result(result, message)
            except Exception as e:
                self._on_thinking_error(str(e))
                
    def _on_thinking_result(self, result: ThinkingResult, original_input: str):
        """思考结果返回"""
        self.is_processing = False
        
        # 保存思考结果
        self.state_manager.save_task({
            'id': self.current_task_id,
            'user_input': original_input,
            'status': TaskStatus.WAITING_INPUT.value,
            'progress': 30,
            'thinking_blueprint': {
                'intent': result.intent.value,
                'confidence': result.intent_confidence,
                'steps': [{
                    'number': s.step_number,
                    'title': s.title,
                    'description': s.description
                } for s in result.thinking_steps]
            }
        })
        
        # 在对话面板嵌入思考画布
        canvas_widget = self.canvas_system.embed_thinking_in_chat(result)
        self.chat_panel.append_thinking_canvas(canvas_widget)
        
        # 更新状态
        self.status_label.setText(f"Intent: {result.intent.value} ({result.intent_confidence:.0%})")
        self.progress_bar.setValue(30)
        
        # 如果不需要蓝图，直接执行
        if not result.context.get('needs_blueprint', True) and result.context.get('direct_response'):
            self.chat_panel.add_message("ai", result.context['direct_response'])
            self._start_execution(original_input)
            
    def _on_thinking_error(self, error: str):
        """思考错误"""
        self.is_processing = False
        self.chat_panel.set_input_enabled(True)
        
        QMessageBox.critical(self, "Error", f"Thinking failed: {error}")
        self.status_label.setText("Error")
        
    def _on_thinking_option_selected(self, option_id: str, option: ThinkingOption):
        """用户选择了思考选项"""
        self.chat_panel.add_message("user", f"Selected option [{option_id}]: {option.title}")
        self.chat_panel.clear_embedded_canvas()
        
        # 更新任务状态
        self.state_manager.update_task_status(
            self.current_task_id,
            TaskStatus.EXECUTING,
            progress=50
        )
        
        # 开始执行
        user_input = self.state_manager.load_task(self.current_task_id).get('user_input', '')
        self._start_execution(user_input)
        
    def _start_execution(self, user_input: str):
        """开始执行"""
        self.status_label.setText("Executing...")
        self.progress_bar.setValue(50)
        self.pause_btn.setEnabled(True)
        
        # 异步启动协调器
        worker = AsyncWorker(self.coordinator.start_task(user_input))
        worker.result_ready.connect(self._on_execution_result)
        worker.error_occurred.connect(self._on_execution_error)
        worker.start()
        
    def _on_execution_result(self, result):
        """执行完成"""
        self.status_label.setText("Completed")
        self.progress_bar.setValue(100)
        self.pause_btn.setEnabled(False)
        self.chat_panel.set_input_enabled(True)
        
        # 更新任务状态
        self.state_manager.update_task_status(
            self.current_task_id,
            TaskStatus.COMPLETED,
            progress=100
        )
        
    def _on_execution_error(self, error: str):
        """执行错误"""
        self.status_label.setText("Failed")
        self.pause_btn.setEnabled(False)
        self.chat_panel.set_input_enabled(True)
        
        self.state_manager.update_task_status(
            self.current_task_id,
            TaskStatus.FAILED
        )
        
        QMessageBox.critical(self, "Execution Error", str(error))
        
    # ===== 协调器回调 =====
    
    def _on_state_change(self, state):
        """状态变化"""
        self.status_label.setText(f"{state.phase} | {state.progress}%")
        self.progress_bar.setValue(state.progress)
        
    def _on_message(self, msg: str):
        """日志消息"""
        # 可以显示在状态栏或其他地方
        pass
        
    def _on_execution_preview(self, preview: dict):
        """执行预览"""
        steps = preview.get('steps', [])
        preview_text = f"<b>Execution Plan ({len(steps)} steps)</b><br>"
        for i, step in enumerate(steps[:5], 1):
            preview_text += f"{i}. {step.get('name', 'Unknown')}<br>"
        if len(steps) > 5:
            preview_text += f"... and {len(steps) - 5} more"
        self.chat_panel.add_message("ai", preview_text)
        
    def _on_question(self, question):
        """需要澄清"""
        self.chat_panel.add_message("ai", f"<b>Question:</b> {question.text}")
        
    def _on_options(self, options):
        """选项"""
        pass  # 已在思考画布中处理
        
    def _on_blueprint_loaded(self, steps):
        """蓝图加载"""
        # 转换步骤格式
        blueprint_data = {
            'steps': [
                {
                    'id': getattr(s, 'id', f'step_{i}'),
                    'name': getattr(s, 'name', f'Step {i}'),
                    'direction': getattr(s, 'direction', ''),
                    'status': getattr(s, 'status', 'pending')
                }
                for i, s in enumerate(steps)
            ]
        }
        
        self.canvas_system.show_execution_blueprint(blueprint_data)
        
        # 保存执行蓝图
        self.state_manager.save_task({
            'id': self.current_task_id,
            'execution_blueprint': blueprint_data,
            'status': TaskStatus.EXECUTING.value
        })
        
    def _on_step_update(self, step_id: str, status: str, index: int):
        """步骤更新"""
        self.canvas_system.update_execution_status(step_id, status)
        
        # 创建检查点
        self.state_manager.create_checkpoint(
            self.current_task_id,
            'executing',
            {'step_id': step_id, 'status': status, 'index': index}
        )
        
    def _on_execution_complete(self, result: dict):
        """执行完成"""
        success = result.get('success', False)
        summary = result.get('summary', 'Execution completed')
        
        icon = "[+]" if success else "[x]"
        self.chat_panel.add_message("ai", f"<h3>{icon} {summary}</h3>")
        
    def _on_intervention_needed(self, step_id: str, reason: str):
        """需要干预"""
        reply = QMessageBox.question(
            self,
            "Intervention Needed",
            f"Step needs intervention: {reason}\n\nRevert to thinking phase?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 重新规划
            worker = AsyncWorker(self.coordinator.handle_intervention("replan"))
            worker.start()
            
    def _on_execution_node_clicked(self, step_id: str):
        """执行节点被点击"""
        print(f"[MainWindow] Node clicked: {step_id}")
        
    def _on_intervention_requested(self, step_id: str, position):
        """请求干预"""
        print(f"[MainWindow] Intervention requested at {step_id}, position: {position}")
        
    # ===== 菜单/工具栏动作 =====
    
    def _on_new_task(self):
        """新任务"""
        self.chat_panel.clear_messages()
        self.chat_panel.clear_embedded_canvas()
        self.canvas_system.execution_canvas.clear()
        self.chat_panel.set_input_enabled(True)
        self.current_task_id = ""
        self.is_processing = False
        self._show_welcome()
        
    def _on_fit_view(self):
        """适应视图"""
        self.canvas_system.execution_canvas.fit_to_view()
        
    def _on_recent_tasks(self):
        """最近任务"""
        tasks = self.state_manager.list_recent_tasks(10)
        
        msg = "<h3>Recent Tasks</h3>"
        for task in tasks:
            msg += f"<p><b>{task.user_input[:30]}...</b><br>"
            msg += f"Status: {task.status} | Progress: {task.progress}%</p>"
            
        self.chat_panel.add_message("ai", msg)
        
    def _on_recover_tasks(self):
        """恢复任务"""
        candidates = self.state_manager.get_recovery_candidates()
        
        if not candidates:
            QMessageBox.information(self, "Recover Tasks", "No recoverable tasks found")
            return
            
        # 简化处理：恢复最新的一个
        task = candidates[0]
        reply = QMessageBox.question(
            self,
            "Recover Task",
            f"Recover task: {task.user_input[:50]}...?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._recover_task(task.id)
            
    def _recover_task(self, task_id: str):
        """恢复指定任务"""
        task_data = self.state_manager.load_task(task_id)
        if not task_data:
            QMessageBox.warning(self, "Error", "Task not found")
            return
            
        # 加载任务到 UI
        self.chat_panel.add_message("user", task_data['user_input'])
        
        # 如果有执行蓝图，显示
        exec_blueprint = task_data.get('execution_blueprint', {})
        if exec_blueprint:
            self.canvas_system.show_execution_blueprint(exec_blueprint)
            
        self.current_task_id = task_id
        self.status_label.setText(f"Recovered: {task_data['status']}")
        
    def _on_pause(self):
        """暂停/继续"""
        if self.coordinator.execution_system.is_paused:
            self.coordinator.execution_system.resume_execution()
            self.pause_btn.setText("Pause")
            self.status_label.setText("Resumed")
        else:
            self.coordinator.execution_system.pause_execution()
            self.pause_btn.setText("Resume")
            self.status_label.setText("Paused")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Blueclaw v1.0")
    parser.add_argument("--llm", action="store_true", help="Use LLM thinking engine")
    parser.add_argument("--api-key", default=None, help="LLM API key")
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 设置应用字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 创建主窗口
    window = BlueclawV1MainWindow(
        use_llm=args.llm,
        llm_api_key=args.api_key
    )
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
