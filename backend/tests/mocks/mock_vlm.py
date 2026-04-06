#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock VLM - 视觉语言模型模拟
不调用真实GPT-4V，返回预设的识别结果
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import List, Dict, Optional
from backend.vis.vlm import UIElement, ElementType


class MockVLM:
    """模拟视觉语言模型"""
    
    def __init__(self):
        self.scenario_elements = {
            "jianying_main": [
                UIElement(
                    id="elem_1",
                    type=ElementType.BUTTON,
                    label="导入",
                    description="导入素材按钮",
                    bbox={"x": 20, "y": 10, "width": 60, "height": 40},
                    confidence=0.95
                ),
                UIElement(
                    id="elem_2",
                    type=ElementType.BUTTON,
                    label="导出",
                    description="导出视频按钮，橙色",
                    bbox={"x": 100, "y": 10, "width": 60, "height": 40},
                    confidence=0.95,
                    state="enabled"
                ),
                UIElement(
                    id="elem_3",
                    type=ElementType.BUTTON,
                    label="视频",
                    description="视频素材按钮",
                    bbox={"x": 20, "y": 150, "width": 100, "height": 40},
                    confidence=0.90
                ),
            ],
            "jianying_export": [
                UIElement(
                    id="elem_export",
                    type=ElementType.BUTTON,
                    label="导出",
                    description="导出确认按钮",
                    bbox={"x": 1000, "y": 700, "width": 200, "height": 50},
                    confidence=0.98
                ),
            ],
            "blender_viewport": [
                UIElement(
                    id="elem_cube",
                    type=ElementType.UNKNOWN,
                    label="立方体",
                    description="默认立方体",
                    bbox={"x": 800, "y": 400, "width": 300, "height": 300},
                    confidence=0.85
                ),
            ],
            "empty": [],
        }
        self.current_scenario = "jianying_main"
    
    def set_scenario(self, scenario: str):
        """设置测试场景"""
        self.current_scenario = scenario
    
    async def analyze_screenshot(self, screenshot_base64: str, task_description: str) -> Dict:
        """返回预设的分析结果"""
        elements = self.scenario_elements.get(self.current_scenario, [])
        
        scenario_types = {
            "jianying_main": "剪映主编辑界面",
            "jianying_export": "导出设置对话框",
            "blender_viewport": "Blender 3D视口",
            "empty": "空白界面",
            "desktop": "桌面",
        }
        
        suggested = elements[0].label if elements else "等待"
        
        return {
            "scene_type": scenario_types.get(self.current_scenario, "未知界面"),
            "elements": elements,
            "current_state": f"当前处于{scenario_types.get(self.current_scenario, '未知')}状态",
            "available_actions": ["点击", "拖拽", "输入"],
            "suggested_next_action": f"点击{suggested}"
        }
    
    async def find_element(self, screenshot_base64: str, description: str) -> Optional[UIElement]:
        """根据描述查找元素"""
        elements = self.scenario_elements.get(self.current_scenario, [])
        
        for elem in elements:
            if elem.label in description or description in elem.description:
                return elem
        
        return elements[0] if elements else None
    
    async def verify_action_result(
        self,
        before_screenshot: str,
        after_screenshot: str,
        expected_change: str
    ) -> Dict:
        """模拟验证结果"""
        return {
            "success": True,
            "observed_change": f"检测到变化: {expected_change}",
            "confidence": 0.92
        }
