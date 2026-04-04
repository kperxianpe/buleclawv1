#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
items.py - Blueclaw v1.0 Canvas Items

画布项定义 - 支持思考小画布和执行大画布的图形元素
"""

from PyQt5.QtWidgets import (
    QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsDropShadowEffect, QGraphicsProxyWidget, QWidget,
    QGraphicsPathItem
)
from PyQt5.QtCore import Qt, QRectF, QPointF, pyqtSignal, QObject
from PyQt5.QtGui import (
    QColor, QPen, QBrush, QFont, QPainter, QPainterPath,
    QLinearGradient, QFontMetrics
)
from PyQt5.QtCore import QPointF
from typing import Tuple, Optional, List, Dict
from dataclasses import dataclass, field
from dataclasses import dataclass
from enum import Enum


class NodeStatus(Enum):
    """节点状态"""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    INTERVENING = "intervening"


@dataclass
class NodeStyle:
    """节点样式配置"""
    bg_color: QColor = field(default_factory=lambda: QColor(30, 30, 30))
    border_color: QColor = field(default_factory=lambda: QColor(107, 114, 128))
    border_width: int = 2
    text_color: QColor = field(default_factory=lambda: QColor(255, 255, 255))
    secondary_text_color: QColor = field(default_factory=lambda: QColor(170, 170, 170))
    corner_radius: int = 8
    shadow_enabled: bool = True
    
    # 状态颜色
    status_colors: Dict[NodeStatus, QColor] = field(default_factory=lambda: {
        NodeStatus.PENDING: QColor(107, 114, 128),
        NodeStatus.ACTIVE: QColor(59, 130, 246),
        NodeStatus.COMPLETED: QColor(16, 185, 129),
        NodeStatus.FAILED: QColor(239, 68, 68),
        NodeStatus.INTERVENING: QColor(245, 158, 11)
    })


class StepNodeItem(QGraphicsRectItem):
    """
    思考步骤节点 - 小画布用
    
    显示思考过程中的单个步骤
    """
    
    clicked = pyqtSignal(str)  # step_id
    
    def __init__(self, step_id: str, title: str, status: str = "pending",
                 description: str = "", parent=None):
        super().__init__(parent)
        
        self.step_id = step_id
        self.title = title
        self.status = NodeStatus(status) if isinstance(status, str) else status
        self.description = description
        self.style = NodeStyle()
        
        # 尺寸设置
        self.node_width = 200
        self.node_height = 70
        self.setRect(0, 0, self.node_width, self.node_height)
        
        # 启用交互
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setAcceptHoverEvents(True)
        
        # 创建文字项
        self._create_text_items()
        
        # 添加阴影效果
        self._setup_shadow()
        
    def _create_text_items(self):
        """创建文字项"""
        # 标题
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setDefaultTextColor(self.style.text_color)
        font = QFont("Microsoft YaHei", 10, QFont.Bold)
        self.title_item.setFont(font)
        self.title_item.setPlainText(self._truncate_text(self.title, 18))
        self.title_item.setPos(10, 10)
        
        # 描述
        if self.description:
            self.desc_item = QGraphicsTextItem(self)
            self.desc_item.setDefaultTextColor(self.style.secondary_text_color)
            font = QFont("Microsoft YaHei", 8)
            self.desc_item.setFont(font)
            self.desc_item.setPlainText(self._truncate_text(self.description, 25))
            self.desc_item.setPos(10, 35)
            
    def _setup_shadow(self):
        """设置阴影效果"""
        if self.style.shadow_enabled:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setColor(QColor(0, 0, 0, 80))
            shadow.setOffset(2, 2)
            # QGraphicsRectItem 不支持 setGraphicsEffect
            # 需要在父级或场景上设置
            
    def _truncate_text(self, text: str, max_chars: int) -> str:
        """截断文本"""
        if len(text) > max_chars:
            return text[:max_chars-3] + "..."
        return text
        
    def paint(self, painter: QPainter, option, widget=None):
        """绘制节点"""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取状态颜色
        border_color = self.style.status_colors.get(
            self.status, self.style.border_color
        )
        
        # 背景渐变
        gradient = QLinearGradient(0, 0, 0, self.node_height)
        gradient.setColorAt(0, QColor(45, 45, 45))
        gradient.setColorAt(1, QColor(35, 35, 35))
        
        # 绘制圆角矩形背景
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(border_color, self.style.border_width))
        
        rect = self.rect()
        painter.drawRoundedRect(rect, self.style.corner_radius, self.style.corner_radius)
        
        # 如果是 active 状态，添加脉冲效果
        if self.status == NodeStatus.ACTIVE:
            self._draw_pulse_effect(painter, rect)
            
        # 绘制状态指示点
        self._draw_status_indicator(painter, border_color)
        
    def _draw_pulse_effect(self, painter: QPainter, rect: QRectF):
        """绘制脉冲效果"""
        pulse_color = QColor(59, 130, 246, 30)
        painter.setBrush(QBrush(pulse_color))
        painter.setPen(Qt.NoPen)
        
        # 外圈光晕
        pulse_rect = rect.adjusted(-4, -4, 4, 4)
        painter.drawRoundedRect(pulse_rect, self.style.corner_radius + 2, 
                                self.style.corner_radius + 2)
        
    def _draw_status_indicator(self, painter: QPainter, color: QColor):
        """绘制状态指示点"""
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        
        # 右上角小圆点
        painter.drawEllipse(self.node_width - 15, 8, 8, 8)
        
    def set_status(self, status: NodeStatus):
        """设置状态"""
        self.status = status
        self.update()
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        self.clicked.emit(self.step_id)
        super().mousePressEvent(event)
        
    def hoverEnterEvent(self, event):
        """鼠标悬停进入"""
        self.setCursor(Qt.PointingHandCursor)
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """鼠标悬停离开"""
        self.unsetCursor()
        super().hoverLeaveEvent(event)


class OptionButtonItem(QGraphicsRectItem):
    """
    四选一选项按钮 - 画布里渲染
    
    在思考画布中以 2x2 网格显示选项
    """
    
    clicked = pyqtSignal(str, object)  # option_id, option_data
    
    def __init__(self, option_id: str, label: str, title: str,
                 description: str, confidence: float, 
                 position: Tuple[int, int], parent=None):
        super().__init__(parent)
        
        self.option_id = option_id
        self.label = label
        self.title = title
        self.description = description
        self.confidence = confidence
        
        # 尺寸和位置
        self.btn_width = 220
        self.btn_height = 70
        self.setRect(0, 0, self.btn_width, self.btn_height)
        self.setPos(position[0], position[1])
        
        # 样式
        self.base_color = QColor(59, 130, 246)
        self.is_selected = False
        self.is_hovered = False
        
        # 启用交互
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)
        
        # 创建文字项
        self._create_text_items()
        
    def _create_text_items(self):
        """创建文字项"""
        # 标签 A/B/C/D
        self.label_item = QGraphicsTextItem(self)
        self.label_item.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Arial", 14, QFont.Bold)
        self.label_item.setFont(font)
        self.label_item.setPlainText(f"[{self.label}]")
        self.label_item.setPos(10, 8)
        
        # 标题
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Microsoft YaHei", 11, QFont.Bold)
        self.title_item.setFont(font)
        self.title_item.setPlainText(self._truncate_text(self.title, 12))
        self.title_item.setPos(50, 8)
        
        # 描述
        self.desc_item = QGraphicsTextItem(self)
        self.desc_item.setDefaultTextColor(QColor(204, 204, 204))
        font = QFont("Microsoft YaHei", 9)
        self.desc_item.setFont(font)
        self.desc_item.setPlainText(self._truncate_text(self.description, 22))
        self.desc_item.setPos(10, 32)
        
        # 置信度文字
        self.conf_item = QGraphicsTextItem(self)
        conf_color = QColor(255, 255, 255)
        self.conf_item.setDefaultTextColor(conf_color)
        font = QFont("Arial", 10, QFont.Bold)
        self.conf_item.setFont(font)
        self.conf_item.setPlainText(f"{int(self.confidence * 100)}%")
        self.conf_item.setPos(self.btn_width - 40, 45)
        
    def _truncate_text(self, text: str, max_chars: int) -> str:
        """截断文本"""
        if len(text) > max_chars:
            return text[:max_chars-3] + "..."
        return text
        
    def paint(self, painter: QPainter, option, widget=None):
        """绘制选项按钮"""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 计算背景透明度（基于置信度）
        base_alpha = int(80 + self.confidence * 100)
        
        # 根据状态调整颜色
        if self.is_selected:
            bg_color = QColor(59, 130, 246, 200)
            border_color = QColor(96, 165, 250)
            border_width = 3
        elif self.is_hovered:
            bg_color = QColor(59, 130, 246, 150)
            border_color = QColor(96, 165, 250)
            border_width = 2
        else:
            bg_color = QColor(59, 130, 246, base_alpha)
            border_color = self.base_color
            border_width = 2
            
        # 绘制背景
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, border_width))
        
        rect = self.rect()
        painter.drawRoundedRect(rect, 6, 6)
        
        # 绘制置信度条
        self._draw_confidence_bar(painter)
        
    def _draw_confidence_bar(self, painter: QPainter):
        """绘制底部置信度条"""
        bar_height = 4
        bar_y = self.btn_height - bar_height - 4
        bar_width = self.btn_width - 20
        
        # 背景条
        painter.setBrush(QBrush(QColor(60, 60, 60)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(10, bar_y, bar_width, bar_height, 2, 2)
        
        # 填充条
        fill_width = int(bar_width * self.confidence)
        fill_color = QColor(96, 165, 250) if self.confidence > 0.7 else QColor(156, 163, 175)
        painter.setBrush(QBrush(fill_color))
        painter.drawRoundedRect(10, bar_y, fill_width, bar_height, 2, 2)
        
    def set_selected(self, selected: bool):
        """设置选中状态"""
        self.is_selected = selected
        self.update()
        
    def mousePressEvent(self, event):
        """鼠标点击"""
        self.clicked.emit(self.option_id, self)
        super().mousePressEvent(event)
        
    def hoverEnterEvent(self, event):
        """鼠标悬停进入"""
        self.is_hovered = True
        self.setCursor(Qt.PointingHandCursor)
        self.update()
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """鼠标悬停离开"""
        self.is_hovered = False
        self.unsetCursor()
        self.update()
        super().hoverLeaveEvent(event)


class ExecutionNodeItem(QGraphicsRectItem):
    """
    执行步骤节点 - 大画布用
    
    显示执行蓝图中的步骤，支持点击干预
    """
    
    clicked = pyqtSignal(str)  # step_id
    intervention_requested = pyqtSignal(str, str)  # step_id, reason
    
    def __init__(self, step_id: str, title: str, direction: str = "",
                 status: str = "pending", position: Tuple[int, int] = (0, 0),
                 parent=None):
        super().__init__(parent)
        
        self.step_id = step_id
        self.title = title
        self.direction = direction
        self.status = NodeStatus(status) if isinstance(status, str) else status
        
        # 尺寸
        self.node_width = 200
        self.node_height = 100
        self.setRect(0, 0, self.node_width, self.node_height)
        self.setPos(position[0], position[1])
        
        # 样式
        self.style = NodeStyle()
        self.pulse_animation_frame = 0
        
        # 启用交互
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, False)
        self.setAcceptHoverEvents(True)
        
        # 创建文字
        self._create_text_items()
        
    def _create_text_items(self):
        """创建文字项"""
        # 步骤标题
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setDefaultTextColor(QColor(255, 255, 255))
        font = QFont("Microsoft YaHei", 12, QFont.Bold)
        self.title_item.setFont(font)
        self.title_item.setPlainText(self._truncate_text(self.title, 18))
        self.title_item.setPos(10, 10)
        
        # 方向说明
        if self.direction:
            self.direction_item = QGraphicsTextItem(self)
            self.direction_item.setDefaultTextColor(QColor(170, 170, 170))
            font = QFont("Microsoft YaHei", 10)
            self.direction_item.setFont(font)
            self.direction_item.setPlainText(self._truncate_text(self.direction, 30))
            self.direction_item.setPos(10, 40)
            
    def _truncate_text(self, text: str, max_chars: int) -> str:
        """截断文本"""
        if len(text) > max_chars:
            return text[:max_chars-3] + "..."
        return text
        
    def paint(self, painter: QPainter, option, widget=None):
        """绘制执行节点"""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 获取状态颜色
        border_color = self.style.status_colors.get(
            self.status, self.style.border_color
        )
        
        # 绘制脉冲效果（running 状态）
        if self.status == NodeStatus.ACTIVE:
            self._draw_pulse_animation(painter)
            
        # 背景
        gradient = QLinearGradient(0, 0, 0, self.node_height)
        gradient.setColorAt(0, QColor(45, 45, 45))
        gradient.setColorAt(1, QColor(35, 35, 35))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(border_color, 2))
        
        rect = self.rect()
        painter.drawRoundedRect(rect, 10, 10)
        
        # 绘制状态图标
        self._draw_status_icon(painter, border_color)
        
        # 如果是 intervening 状态，绘制警告边框
        if self.status == NodeStatus.INTERVENING:
            self._draw_intervention_border(painter)
            
    def _draw_pulse_animation(self, painter: QPainter):
        """绘制脉冲动画效果"""
        # 动态透明度
        alpha = int(30 + 20 * (self.pulse_animation_frame % 10) / 10)
        pulse_color = QColor(59, 130, 246, alpha)
        
        painter.setBrush(QBrush(pulse_color))
        painter.setPen(Qt.NoPen)
        
        pulse_rect = self.rect().adjusted(-6, -6, 6, 6)
        painter.drawRoundedRect(pulse_rect, 12, 12)
        
        # 更新动画帧
        self.pulse_animation_frame += 1
        
    def _draw_status_icon(self, painter: QPainter, color: QColor):
        """绘制状态图标"""
        icons = {
            NodeStatus.PENDING: "[ ]",
            NodeStatus.ACTIVE: "[~]",
            NodeStatus.COMPLETED: "[+]",
            NodeStatus.FAILED: "[x]",
            NodeStatus.INTERVENING: "[!]"
        }
        
        icon = icons.get(self.status, "[?]")
        
        painter.setPen(color)
        font = QFont("Arial", 16)
        painter.setFont(font)
        painter.drawText(int(self.node_width - 30), 30, icon)
        
    def _draw_intervention_border(self, painter: QPainter):
        """绘制干预状态边框"""
        dash_pen = QPen(QColor(245, 158, 11), 3)
        dash_pen.setStyle(Qt.DashLine)
        painter.setPen(dash_pen)
        painter.setBrush(Qt.NoBrush)
        
        rect = self.rect().adjusted(-3, -3, 3, 3)
        painter.drawRoundedRect(rect, 12, 12)
        
    def set_status(self, status: NodeStatus):
        """设置状态"""
        self.status = status
        self.update()
        
    def update_pulse_animation(self):
        """更新脉冲动画（需要定时器调用）"""
        if self.status == NodeStatus.ACTIVE:
            self.update()
            
    def mousePressEvent(self, event):
        """鼠标点击 - 触发干预"""
        self.clicked.emit(self.step_id)
        super().mousePressEvent(event)
        
    def hoverEnterEvent(self, event):
        """鼠标悬停进入"""
        self.setCursor(Qt.PointingHandCursor)
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """鼠标悬停离开"""
        self.unsetCursor()
        super().hoverLeaveEvent(event)


class ConnectionItem(QGraphicsPathItem):
    """
    连接线条 - 连接节点
    """
    
    def __init__(self, source_item: QGraphicsItem, target_item: QGraphicsItem,
                 parent=None):
        super().__init__(parent)
        
        self.source_item = source_item
        self.target_item = target_item
        
        # 样式
        self.line_color = QColor(107, 114, 128)
        self.line_width = 2
        self.arrow_size = 10
        
        self.update_path()
        
    def update_path(self):
        """更新连接路径"""
        # 获取源和目标的位置
        src_rect = self.source_item.sceneBoundingRect()
        tgt_rect = self.target_item.sceneBoundingRect()
        
        # 起点：源节点底部中心
        start = QPointF(
            src_rect.center().x(),
            src_rect.bottom()
        )
        
        # 终点：目标节点顶部中心
        end = QPointF(
            tgt_rect.center().x(),
            tgt_rect.top()
        )
        
        # 创建曲线路径
        path = QPainterPath()
        path.moveTo(start)
        
        # 贝塞尔曲线控制点
        ctrl1 = QPointF(start.x(), start.y() + 30)
        ctrl2 = QPointF(end.x(), end.y() - 30)
        
        path.cubicTo(ctrl1, ctrl2, end)
        
        self.setPath(path)
        
    def paint(self, painter: QPainter, option, widget=None):
        """绘制连接线"""
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制曲线
        pen = QPen(self.line_color, self.line_width)
        painter.setPen(pen)
        painter.drawPath(self.path())
        
        # 绘制箭头
        self._draw_arrow(painter)
        
    def _draw_arrow(self, painter: QPainter):
        """绘制箭头"""
        path = self.path()
        end_point = path.pointAtPercent(1.0)
        
        # 计算角度
        angle = path.angleAtPercent(1.0)
        
        # 箭头三角形
        arrow_path = QPainterPath()
        arrow_path.moveTo(end_point)
        
        rad = 3.14159 / 180
        arrow_p1 = QPointF(
            end_point.x() - self.arrow_size * (1),
            end_point.y() - self.arrow_size * (0.5)
        )
        arrow_p2 = QPointF(
            end_point.x() - self.arrow_size * (1),
            end_point.y() + self.arrow_size * (0.5)
        )
        
        arrow_path.lineTo(arrow_p1)
        arrow_path.lineTo(arrow_p2)
        arrow_path.closeSubpath()
        
        painter.fillPath(arrow_path, QBrush(self.line_color))
