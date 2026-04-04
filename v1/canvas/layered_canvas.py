#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
layered_canvas.py - Blueclaw v1.0 Layered Canvas System

分层画布系统 - V1.0 核心 UI 架构
- 思考蓝图：小画布嵌入对话
- 执行蓝图：大画布主工作区
- 画布交互：模块位置感知、按钮点击、状态同步
"""

from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsProxyWidget
)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QPainter, QFont, QWheelEvent, QPen
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.thinking_engine import ThinkingResult, ThinkingStep, ThinkingOption
from .items import (
    StepNodeItem, OptionButtonItem, ExecutionNodeItem,
    ConnectionItem, NodeStatus
)


@dataclass
class CanvasConfig:
    """画布配置"""
    # 思考小画布
    thinking_canvas_width: int = 600
    thinking_canvas_height: int = 350
    
    # 执行大画布
    execution_canvas_min_width: int = 800
    execution_canvas_min_height: int = 600
    
    # 颜色主题
    bg_color: str = "#1e1e1e"
    grid_color: str = "#2d2d2d"
    
    # 动画
    animation_enabled: bool = True
    pulse_animation_interval: int = 100  # ms


class ThinkingCanvas(QGraphicsView):
    """
    思考蓝图小画布 - 嵌入对话面板
    
    特点：
    - 固定尺寸（小）
    - 显示思考步骤
    - 2x2 四选项渲染
    """
    
    option_selected = pyqtSignal(str, object)  # option_id, option_data
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.config = CanvasConfig()
        
        # 创建场景
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, self.config.thinking_canvas_width, 
                                self.config.thinking_canvas_height)
        self.setScene(self.scene)
        
        # 设置尺寸
        self.setFixedSize(self.config.thinking_canvas_width, 
                         self.config.thinking_canvas_height)
        
        # 样式
        self.setStyleSheet(f"background: {self.config.bg_color}; border-radius: 8px;")
        self.setRenderHint(QPainter.Antialiasing)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # 存储项
        self.step_items: Dict[str, StepNodeItem] = {}
        self.option_items: Dict[str, OptionButtonItem] = {}
        self.current_result: Optional[ThinkingResult] = None
        
        # 标题
        self._setup_header()
        
    def _setup_header(self):
        """设置画布标题"""
        self.header_label = self.scene.addText("Thinking Blueprint")
        self.header_label.setDefaultTextColor(QColor(159, 173, 189))
        font = QFont("Microsoft YaHei", 12, QFont.Bold)
        self.header_label.setFont(font)
        self.header_label.setPos(20, 10)
        
    def clear(self):
        """清空画布"""
        self.scene.clear()
        self.step_items.clear()
        self.option_items.clear()
        self._setup_header()
        
    def render_thinking_result(self, result: ThinkingResult):
        """渲染思考结果"""
        self.current_result = result
        self.clear()
        
        # 渲染思考步骤（垂直排列）
        y_pos = 50
        for idx, step in enumerate(result.thinking_steps[:3]):  # 最多显示3步
            x_pos = 20 + idx * 210
            
            node = StepNodeItem(
                step_id=f"step_{idx}",
                title=step.title,
                status=step.status,
                description=step.description[:30] if step.description else ""
            )
            node.setPos(x_pos, y_pos)
            self.scene.addItem(node)
            self.step_items[f"step_{idx}"] = node
            
        # 如果有选项，渲染四选一
        if result.options:
            self.render_four_options(result.options)
            
    def render_four_options(self, options: List[ThinkingOption]):
        """渲染四选一选项 - 2x2 网格布局"""
        # 清除旧选项
        for item in self.option_items.values():
            self.scene.removeItem(item)
        self.option_items.clear()
        
        # 2x2 网格位置
        positions = [
            (20, 140),    # A - 左上
            (260, 140),   # B - 右上
            (20, 220),    # C - 左下
            (260, 220)    # D - 右下
        ]
        
        labels = ['A', 'B', 'C', 'D']
        
        for idx, (option, pos, label) in enumerate(zip(options, positions, labels)):
            btn = OptionButtonItem(
                option_id=option.option_id,
                label=label,
                title=option.title,
                description=option.description,
                confidence=option.confidence / 100.0,
                position=pos
            )
            btn.clicked.connect(self._on_option_clicked)
            self.scene.addItem(btn)
            self.option_items[option.option_id] = btn
            
    def _on_option_clicked(self, option_id: str, option_item: OptionButtonItem):
        """选项被点击"""
        # 更新选中状态
        for item in self.option_items.values():
            item.set_selected(False)
        option_item.set_selected(True)
        
        # 发射信号
        if self.current_result:
            option = self.current_result.get_option(option_id)
            if option:
                self.option_selected.emit(option_id, option)
                
    def update_step_status(self, step_id: str, status: str):
        """更新步骤状态"""
        if step_id in self.step_items:
            self.step_items[step_id].set_status(NodeStatus(status))
            
    def get_widget(self) -> QWidget:
        """获取画布控件（用于嵌入）"""
        return self


class ExecutionCanvas(QGraphicsView):
    """
    执行蓝图大画布 - 主工作区
    
    特点：
    - 大尺寸，可缩放
    - 纵向流程布局
    - 支持点击干预
    """
    
    node_clicked = pyqtSignal(str)  # step_id
    intervention_requested = pyqtSignal(str, QPointF)  # step_id, position
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.config = CanvasConfig()
        
        # 创建场景
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        # 设置最小尺寸
        self.setMinimumSize(self.config.execution_canvas_min_width,
                           self.config.execution_canvas_min_height)
        
        # 样式
        self.setStyleSheet(f"background: {self.config.bg_color};")
        self.setRenderHint(QPainter.Antialiasing)
        
        # 启用拖拽、缩放
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        
        # 存储项
        self.node_items: Dict[str, ExecutionNodeItem] = {}
        self.connections: List[ConnectionItem] = []
        self.blueprint_data: Optional[Any] = None
        
        # 动画定时器
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._update_animations)
        self.animation_timer.start(self.config.pulse_animation_interval)
        
        # 绘制网格背景
        self._draw_grid = True
        
    def clear(self):
        """清空画布"""
        self.scene.clear()
        self.node_items.clear()
        self.connections.clear()
        self.blueprint_data = None
        
    def render_execution_blueprint(self, blueprint: Any):
        """渲染执行蓝图"""
        self.clear()
        self.blueprint_data = blueprint
        
        # 获取步骤列表
        steps = getattr(blueprint, 'steps', [])
        if not steps and isinstance(blueprint, list):
            steps = blueprint
            
        if not steps:
            # 显示空状态
            self._show_empty_state()
            return
            
        # 纵向轮次布局
        y_start = 50
        y_step = 150
        x_center = 400
        
        prev_node = None
        
        for idx, step in enumerate(steps):
            y_pos = y_start + idx * y_step
            
            # 根据索引水平偏移（Z字形）
            if idx % 2 == 0:
                x_pos = x_center - 100
            else:
                x_pos = x_center + 100
                
            # 创建执行节点
            step_id = getattr(step, 'id', f"step_{idx}")
            title = getattr(step, 'name', f"Step {idx+1}")
            direction = getattr(step, 'direction', '')
            status = getattr(step, 'status', 'pending')
            
            node = ExecutionNodeItem(
                step_id=step_id,
                title=title,
                direction=direction,
                status=status,
                position=(x_pos, y_pos)
            )
            node.clicked.connect(self._on_node_clicked)
            self.scene.addItem(node)
            self.node_items[step_id] = node
            
            # 连接步骤
            if prev_node:
                conn = ConnectionItem(prev_node, node)
                self.scene.addItem(conn)
                self.connections.append(conn)
                
            prev_node = node
            
        # 调整场景大小
        self._adjust_scene_rect()
        
    def _show_empty_state(self):
        """显示空状态"""
        text = self.scene.addText("Execution Blueprint\n\nNo active execution")
        text.setDefaultTextColor(QColor(107, 114, 128))
        font = QFont("Microsoft YaHei", 14)
        text.setFont(font)
        text.setPos(250, 200)
        
    def _on_node_clicked(self, step_id: str):
        """节点被点击"""
        self.node_clicked.emit(step_id)
        
        # 获取节点位置，用于显示干预面板
        if step_id in self.node_items:
            node = self.node_items[step_id]
            scene_pos = node.scenePos()
            self.intervention_requested.emit(step_id, scene_pos)
            
    def update_node_status(self, step_id: str, status: str):
        """更新节点状态"""
        if step_id in self.node_items:
            self.node_items[step_id].set_status(NodeStatus(status))
            
    def highlight_node(self, step_id: str):
        """高亮节点"""
        if step_id in self.node_items:
            node = self.node_items[step_id]
            # 将节点移到视图中心
            self.centerOn(node)
            
    def _update_animations(self):
        """更新动画"""
        for node in self.node_items.values():
            node.update_pulse_animation()
            
    def _adjust_scene_rect(self):
        """调整场景矩形"""
        if self.node_items:
            rect = self.scene.itemsBoundingRect()
            padding = 50
            self.scene.setSceneRect(
                rect.x() - padding,
                rect.y() - padding,
                rect.width() + padding * 2,
                rect.height() + padding * 2
            )
            
    def fit_to_view(self):
        """适应视图"""
        if self.node_items:
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)
            
    def wheelEvent(self, event: QWheelEvent):
        """鼠标滚轮 - 缩放"""
        if event.modifiers() & Qt.ControlModifier:
            # 缩放
            delta = event.angleDelta().y()
            zoom_factor = 1.1 if delta > 0 else 0.9
            self.scale(zoom_factor, zoom_factor)
        else:
            super().wheelEvent(event)
            
    def drawBackground(self, painter: QPainter, rect: QRectF):
        """绘制背景"""
        super().drawBackground(painter, rect)
        
        if self._draw_grid:
            self._draw_grid_background(painter, rect)
            
    def _draw_grid_background(self, painter: QPainter, rect: QRectF):
        """绘制网格背景"""
        grid_size = 20
        grid_color = QColor(45, 45, 45)
        
        left = int(rect.left()) - (int(rect.left()) % grid_size)
        top = int(rect.top()) - (int(rect.top()) % grid_size)
        right = int(rect.right())
        bottom = int(rect.bottom())
        
        painter.setPen(QPen(grid_color, 1))
        
        # 绘制垂直线
        x = left
        while x < right:
            painter.drawLine(x, top, x, bottom)
            x += grid_size
            
        # 绘制水平线
        y = top
        while y < bottom:
            painter.drawLine(left, y, right, y)
            y += grid_size


class LayeredCanvasSystem:
    """
    分层画布系统 - V1.0 核心 UI 架构
    
    管理三层画布：
    1. 思考画布（小）- 嵌入对话
    2. 执行画布（大）- 主工作区
    3. 预览画布（浮动）- 提示信息
    """
    
    def __init__(self):
        self.thinking_canvas = ThinkingCanvas()
        self.execution_canvas = ExecutionCanvas()
        
        # 连接信号
        self._connect_signals()
        
    def _connect_signals(self):
        """连接信号"""
        # 思考画布选项选择 -> 可以在这里处理
        self.thinking_canvas.option_selected.connect(self._on_thinking_option_selected)
        
        # 执行画布节点点击
        self.execution_canvas.node_clicked.connect(self._on_execution_node_clicked)
        
    def embed_thinking_in_chat(self, thinking_result: ThinkingResult) -> QWidget:
        """
        在对话面板中嵌入思考蓝图小画布
        
        Args:
            thinking_result: 思考引擎结果
            
        Returns:
            画布控件，可嵌入到对话面板
        """
        self.thinking_canvas.render_thinking_result(thinking_result)
        return self.thinking_canvas.get_widget()
        
    def show_execution_blueprint(self, blueprint: Any):
        """
        在主工作区显示执行蓝图大画布
        
        Args:
            blueprint: 执行蓝图数据
        """
        self.execution_canvas.render_execution_blueprint(blueprint)
        
    def update_execution_status(self, step_id: str, status: str):
        """更新执行状态"""
        self.execution_canvas.update_node_status(step_id, status)
        
    def highlight_execution_step(self, step_id: str):
        """高亮执行步骤"""
        self.execution_canvas.highlight_node(step_id)
        
    def _on_thinking_option_selected(self, option_id: str, option_data: Any):
        """思考选项被选中"""
        print(f"[LayeredCanvasSystem] Option selected: {option_id} - {option_data}")
        
    def _on_execution_node_clicked(self, step_id: str):
        """执行节点被点击"""
        print(f"[LayeredCanvasSystem] Node clicked: {step_id}")
        
    def get_thinking_canvas(self) -> ThinkingCanvas:
        """获取思考画布"""
        return self.thinking_canvas
        
    def get_execution_canvas(self) -> ExecutionCanvas:
        """获取执行画布"""
        return self.execution_canvas


# 便捷函数
def create_layered_canvas_system() -> LayeredCanvasSystem:
    """创建分层画布系统"""
    return LayeredCanvasSystem()
