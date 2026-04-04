#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
position_awareness.py - Blueclaw v1.0 Canvas Position Awareness

画布位置感知 - 读取画布内模块位置和按钮坐标
为 V2.0 Adapter 铺垫
"""

from PyQt5.QtWidgets import QGraphicsView, QGraphicsItem
from PyQt5.QtCore import QRectF, QPointF, Qt
from PyQt5.QtGui import QColor
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class ElementType(Enum):
    """元素类型"""
    STEP_NODE = "step_node"
    EXECUTION_NODE = "execution_node"
    OPTION_BUTTON = "option_button"
    CONNECTION = "connection"
    TEXT = "text"
    UNKNOWN = "unknown"


@dataclass
class ElementInfo:
    """画布元素信息"""
    element_id: str
    element_type: str
    position: Tuple[float, float]
    size: Tuple[float, float]
    bounding_box: Tuple[float, float, float, float]  # x, y, w, h
    is_clickable: bool
    text: str
    status: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "element_id": self.element_id,
            "element_type": self.element_type,
            "position": self.position,
            "size": self.size,
            "bounding_box": self.bounding_box,
            "is_clickable": self.is_clickable,
            "text": self.text,
            "status": self.status,
            "metadata": self.metadata
        }


@dataclass
class ConnectionInfo:
    """连接信息"""
    source_id: str
    target_id: str
    connection_type: str = "default"
    
    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "connection_type": self.connection_type
        }


@dataclass
class LayoutSnapshot:
    """布局快照"""
    canvas_size: Tuple[int, int]
    elements: List[ElementInfo]
    connections: List[ConnectionInfo]
    timestamp: datetime
    snapshot_id: str = ""
    
    def __post_init__(self):
        if not self.snapshot_id:
            self.snapshot_id = f"snap_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]}"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "snapshot_id": self.snapshot_id,
            "canvas_size": self.canvas_size,
            "elements": [e.to_dict() for e in self.elements],
            "connections": [c.to_dict() for c in self.connections],
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def get_clickable_elements(self) -> List[ElementInfo]:
        """获取可点击元素"""
        return [e for e in self.elements if e.is_clickable]
    
    def get_elements_by_type(self, element_type: ElementType) -> List[ElementInfo]:
        """按类型获取元素"""
        return [e for e in self.elements if e.element_type == element_type.value]
    
    def get_element_by_id(self, element_id: str) -> Optional[ElementInfo]:
        """按ID获取元素"""
        for e in self.elements:
            if e.element_id == element_id:
                return e
        return None


class CanvasPositionAwareness:
    """
    画布位置感知 - 读取画布内模块位置和按钮
    
    功能：
    1. 扫描画布上所有可交互元素
    2. 获取指定位置的元素
    3. 识别可点击按钮
    4. 导出布局快照（供 V2.0 Adapter 使用）
    """
    
    def __init__(self, canvas: QGraphicsView):
        self.canvas = canvas
        self.element_registry: Dict[str, ElementInfo] = {}
        self.last_snapshot: Optional[LayoutSnapshot] = None
        
    def scan_canvas_elements(self) -> List[ElementInfo]:
        """
        扫描画布上所有可交互元素
        
        Returns:
            元素信息列表
        """
        elements = []
        self.element_registry.clear()
        
        scene = self.canvas.scene()
        if not scene:
            return elements
            
        for item in scene.items():
            element_info = self._parse_item(item)
            if element_info:
                elements.append(element_info)
                self.element_registry[element_info.element_id] = element_info
                
        return elements
    
    def _parse_item(self, item: QGraphicsItem) -> Optional[ElementInfo]:
        """解析图形项为元素信息"""
        # 获取项类型
        item_type = type(item).__name__
        
        # 获取位置和边界
        scene_pos = item.scenePos()
        bounding_rect = item.boundingRect()
        
        # 尝试获取 ID
        element_id = getattr(item, 'step_id', None) or \
                     getattr(item, 'option_id', None) or \
                     str(id(item))
        
        # 尝试获取文本
        text = ""
        if hasattr(item, 'title'):
            text = item.title
        elif hasattr(item, 'label'):
            text = f"[{item.label}]"
        
        # 尝试获取状态
        status = None
        if hasattr(item, 'status'):
            status_value = item.status
            status = status_value.value if hasattr(status_value, 'value') else str(status_value)
        
        # 确定元素类型
        element_type = self._determine_element_type(item)
        
        # 确定是否可点击
        is_clickable = hasattr(item, 'clicked') or \
                       hasattr(item, 'mousePressEvent')
        
        # 收集元数据
        metadata = {}
        for attr in ['confidence', 'description', 'direction']:
            if hasattr(item, attr):
                metadata[attr] = getattr(item, attr)
        
        return ElementInfo(
            element_id=element_id,
            element_type=element_type.value,
            position=(scene_pos.x(), scene_pos.y()),
            size=(bounding_rect.width(), bounding_rect.height()),
            bounding_box=(
                scene_pos.x() + bounding_rect.x(),
                scene_pos.y() + bounding_rect.y(),
                bounding_rect.width(),
                bounding_rect.height()
            ),
            is_clickable=is_clickable,
            text=text,
            status=status,
            metadata=metadata
        )
    
    def _determine_element_type(self, item: QGraphicsItem) -> ElementType:
        """确定元素类型"""
        item_type = type(item).__name__
        
        type_mapping = {
            'StepNodeItem': ElementType.STEP_NODE,
            'ExecutionNodeItem': ElementType.EXECUTION_NODE,
            'OptionButtonItem': ElementType.OPTION_BUTTON,
            'ConnectionItem': ElementType.CONNECTION,
        }
        
        return type_mapping.get(item_type, ElementType.UNKNOWN)
    
    def get_element_at_position(self, x: float, y: float) -> Optional[ElementInfo]:
        """
        获取指定位置的元素
        
        Args:
            x: 场景 X 坐标
            y: 场景 Y 坐标
            
        Returns:
            元素信息，如果没有则返回 None
        """
        # 确保有最新扫描
        if not self.element_registry:
            self.scan_canvas_elements()
            
        # 查找包含该位置的元素
        for element in self.element_registry.values():
            bx, by, bw, bh = element.bounding_box
            if bx <= x <= bx + bw and by <= y <= by + bh:
                return element
                
        return None
    
    def get_clickable_buttons(self) -> List[ElementInfo]:
        """
        获取所有可点击按钮
        
        Returns:
            可点击元素列表
        """
        if not self.element_registry:
            self.scan_canvas_elements()
            
        return [
            info for info in self.element_registry.values()
            if info.is_clickable and info.element_type in [
                ElementType.OPTION_BUTTON.value,
                ElementType.EXECUTION_NODE.value,
                ElementType.STEP_NODE.value
            ]
        ]
    
    def get_option_buttons(self) -> List[ElementInfo]:
        """获取所有选项按钮（A/B/C/D）"""
        if not self.element_registry:
            self.scan_canvas_elements()
            
        return [
            info for info in self.element_registry.values()
            if info.element_type == ElementType.OPTION_BUTTON.value
        ]
    
    def get_execution_nodes(self) -> List[ElementInfo]:
        """获取所有执行节点"""
        if not self.element_registry:
            self.scan_canvas_elements()
            
        return [
            info for info in self.element_registry.values()
            if info.element_type == ElementType.EXECUTION_NODE.value
        ]
    
    def export_layout_snapshot(self) -> LayoutSnapshot:
        """
        导出画布布局快照 - 供 V2.0 Adapter 使用
        
        Returns:
            布局快照对象
        """
        elements = self.scan_canvas_elements()
        connections = self._extract_connections()
        
        canvas_size = (self.canvas.width(), self.canvas.height())
        
        self.last_snapshot = LayoutSnapshot(
            canvas_size=canvas_size,
            elements=elements,
            connections=connections,
            timestamp=datetime.now()
        )
        
        return self.last_snapshot
    
    def _extract_connections(self) -> List[ConnectionInfo]:
        """提取连接信息"""
        connections = []
        scene = self.canvas.scene()
        
        if not scene:
            return connections
            
        for item in scene.items():
            if type(item).__name__ == 'ConnectionItem':
                source_id = getattr(getattr(item, 'source_item', None), 'step_id', None)
                target_id = getattr(getattr(item, 'target_item', None), 'step_id', None)
                
                if source_id and target_id:
                    connections.append(ConnectionInfo(
                        source_id=source_id,
                        target_id=target_id
                    ))
                    
        return connections
    
    def save_snapshot_to_file(self, filepath: str) -> bool:
        """
        保存快照到文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            是否成功
        """
        try:
            snapshot = self.export_layout_snapshot()
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(snapshot.to_json())
            return True
        except Exception as e:
            print(f"[CanvasPositionAwareness] Failed to save snapshot: {e}")
            return False
    
    def get_element_center(self, element_id: str) -> Optional[Tuple[float, float]]:
        """
        获取元素中心点坐标
        
        Args:
            element_id: 元素 ID
            
        Returns:
            (x, y) 中心点坐标
        """
        element = self.element_registry.get(element_id)
        if not element:
            return None
            
        x, y, w, h = element.bounding_box
        return (x + w / 2, y + h / 2)
    
    def get_element_screen_position(self, element_id: str) -> Optional[Tuple[int, int]]:
        """
        获取元素在屏幕上的位置
        
        Args:
            element_id: 元素 ID
            
        Returns:
            (x, y) 屏幕坐标
        """
        element = self.element_registry.get(element_id)
        if not element:
            return None
            
        # 场景坐标
        scene_x, scene_y = element.position
        
        # 转换为视图坐标
        view_pos = self.canvas.mapFromScene(scene_x, scene_y)
        
        # 转换为全局屏幕坐标
        global_pos = self.canvas.mapToGlobal(view_pos)
        
        return (global_pos.x(), global_pos.y())
    
    def find_element_by_text(self, text: str) -> Optional[ElementInfo]:
        """
        通过文本查找元素
        
        Args:
            text: 要查找的文本
            
        Returns:
            匹配的元素
        """
        if not self.element_registry:
            self.scan_canvas_elements()
            
        for element in self.element_registry.values():
            if text.lower() in element.text.lower():
                return element
                
        return None
    
    def get_active_elements(self) -> List[ElementInfo]:
        """获取当前活动的元素（status == active/running）"""
        if not self.element_registry:
            self.scan_canvas_elements()
            
        return [
            e for e in self.element_registry.values()
            if e.status in ['active', 'running', 'ACTVE', 'RUNNING']
        ]


class CanvasElementLocator:
    """
    画布元素定位器 - 高级定位功能
    
    提供多种策略来定位画布上的元素
    """
    
    def __init__(self, awareness: CanvasPositionAwareness):
        self.awareness = awareness
        
    def locate_option_by_label(self, label: str) -> Optional[ElementInfo]:
        """
        通过标签定位选项按钮（A/B/C/D）
        
        Args:
            label: 标签字母
            
        Returns:
            选项按钮元素
        """
        options = self.awareness.get_option_buttons()
        
        for opt in options:
            # 检查元数据中的 label
            opt_label = opt.metadata.get('label', '')
            if opt_label.upper() == label.upper():
                return opt
                
            # 检查文本内容
            if f"[{label.upper()}]" in opt.text:
                return opt
                
        return None
    
    def locate_execution_step(self, step_name: str) -> Optional[ElementInfo]:
        """
        通过名称定位执行步骤
        
        Args:
            step_name: 步骤名称
            
        Returns:
            执行节点元素
        """
        nodes = self.awareness.get_execution_nodes()
        
        for node in nodes:
            if step_name.lower() in node.text.lower():
                return node
                
        return None
    
    def locate_by_confidence_threshold(self, threshold: float = 0.7) -> List[ElementInfo]:
        """
        定位置信度超过阈值的元素
        
        Args:
            threshold: 置信度阈值（0-1）
            
        Returns:
            符合条件的元素列表
        """
        elements = self.awareness.scan_canvas_elements()
        
        result = []
        for e in elements:
            confidence = e.metadata.get('confidence', 0)
            if isinstance(confidence, (int, float)) and confidence >= threshold:
                result.append(e)
                
        return result
    
    def get_best_option(self) -> Optional[ElementInfo]:
        """获取置信度最高的选项"""
        options = self.awareness.get_option_buttons()
        
        if not options:
            return None
            
        # 按置信度排序
        return max(options, key=lambda e: e.metadata.get('confidence', 0))


# 便捷函数
def create_position_awareness(canvas: QGraphicsView) -> CanvasPositionAwareness:
    """创建位置感知器"""
    return CanvasPositionAwareness(canvas)


def create_element_locator(awareness: CanvasPositionAwareness) -> CanvasElementLocator:
    """创建元素定位器"""
    return CanvasElementLocator(awareness)
