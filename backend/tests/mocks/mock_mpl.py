#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock MPL - 动作原语模拟
不执行真实鼠标键盘操作，记录操作日志
"""
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.vis.mpl import ActionResult


@dataclass
class RecordedAction:
    """记录的动作"""
    action_type: str
    coordinates: Optional[Tuple[int, int]]
    params: Dict
    timestamp: float = field(default_factory=time.time)


class MockMPL:
    """模拟动作原语库"""
    
    def __init__(self):
        self.recorded_actions: List[RecordedAction] = []
        self.mock_position = (960, 540)  # 模拟当前鼠标位置
    
    async def click(self, x: int, y: int, duration: float = 0.5) -> ActionResult:
        """记录点击动作"""
        self.recorded_actions.append(RecordedAction(
            action_type="click",
            coordinates=(x, y),
            params={"duration": duration}
        ))
        self.mock_position = (x, y)
        
        return ActionResult(
            success=True,
            action_type="click",
            coordinates=(x, y),
            message=f"[MOCK] Clicked at ({x}, {y})",
            duration_ms=duration * 1000
        )
    
    async def double_click(self, x: int, y: int, duration: float = 0.5) -> ActionResult:
        """记录双击动作"""
        self.recorded_actions.append(RecordedAction(
            action_type="double_click",
            coordinates=(x, y),
            params={"duration": duration}
        ))
        self.mock_position = (x, y)
        
        return ActionResult(
            success=True,
            action_type="double_click",
            coordinates=(x, y),
            message=f"[MOCK] Double-clicked at ({x}, {y})",
            duration_ms=duration * 1000
        )
    
    async def right_click(self, x: int, y: int, duration: float = 0.5) -> ActionResult:
        """记录右键单击"""
        self.recorded_actions.append(RecordedAction(
            action_type="right_click",
            coordinates=(x, y),
            params={"duration": duration}
        ))
        self.mock_position = (x, y)
        
        return ActionResult(
            success=True,
            action_type="right_click",
            coordinates=(x, y),
            message=f"[MOCK] Right-clicked at ({x}, {y})",
            duration_ms=duration * 1000
        )
    
    async def drag(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        duration: float = 0.5
    ) -> ActionResult:
        """记录拖拽动作"""
        self.recorded_actions.append(RecordedAction(
            action_type="drag",
            coordinates=(end_x, end_y),
            params={"start": (start_x, start_y), "end": (end_x, end_y), "duration": duration}
        ))
        self.mock_position = (end_x, end_y)
        
        return ActionResult(
            success=True,
            action_type="drag",
            coordinates=(end_x, end_y),
            message=f"[MOCK] Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})",
            duration_ms=duration * 1000
        )
    
    async def scroll(self, amount: int, x: Optional[int] = None, y: Optional[int] = None) -> ActionResult:
        """记录滚动动作"""
        pos = (x, y) if x else self.mock_position
        self.recorded_actions.append(RecordedAction(
            action_type="scroll",
            coordinates=pos,
            params={"amount": amount}
        ))
        
        return ActionResult(
            success=True,
            action_type="scroll",
            coordinates=pos,
            message=f"[MOCK] Scrolled {amount}",
            duration_ms=100
        )
    
    async def type_text(self, text: str, interval: float = 0.01) -> ActionResult:
        """记录输入动作"""
        self.recorded_actions.append(RecordedAction(
            action_type="type",
            coordinates=self.mock_position,
            params={"text": text[:50], "interval": interval}
        ))
        
        return ActionResult(
            success=True,
            action_type="type",
            coordinates=self.mock_position,
            message=f"[MOCK] Typed: {text[:20]}...",
            duration_ms=len(text) * interval * 1000
        )
    
    async def keypress(self, keys: list) -> ActionResult:
        """记录按键动作"""
        self.recorded_actions.append(RecordedAction(
            action_type="keypress",
            coordinates=self.mock_position,
            params={"keys": keys}
        ))
        
        return ActionResult(
            success=True,
            action_type="keypress",
            coordinates=self.mock_position,
            message=f"[MOCK] Pressed: {'+'.join(keys)}",
            duration_ms=100
        )
    
    async def hover(self, x: int, y: int, duration: float = 0.5) -> ActionResult:
        """记录悬停动作"""
        self.recorded_actions.append(RecordedAction(
            action_type="hover",
            coordinates=(x, y),
            params={"duration": duration}
        ))
        self.mock_position = (x, y)
        
        return ActionResult(
            success=True,
            action_type="hover",
            coordinates=(x, y),
            message=f"[MOCK] Hovered at ({x}, {y})",
            duration_ms=duration * 1000
        )
    
    async def wait(self, seconds: float) -> ActionResult:
        """记录等待动作"""
        import asyncio
        await asyncio.sleep(seconds * 0.1)  # 测试时加速
        
        self.recorded_actions.append(RecordedAction(
            action_type="wait",
            coordinates=self.mock_position,
            params={"seconds": seconds}
        ))
        
        return ActionResult(
            success=True,
            action_type="wait",
            coordinates=self.mock_position,
            message=f"[MOCK] Waited {seconds}s",
            duration_ms=seconds * 1000
        )
    
    def get_actions(self) -> List[RecordedAction]:
        """获取所有记录的动作"""
        return self.recorded_actions.copy()
    
    def clear_actions(self):
        """清空记录"""
        self.recorded_actions.clear()
