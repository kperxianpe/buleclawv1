#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mock VMS - 视觉记忆系统模拟
不调用真实截图API，返回预设/生成的假截图
"""
import io
import base64
from typing import Optional, Tuple, List
from dataclasses import dataclass
import uuid

try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.vis.vms import Screenshot


class MockVMS:
    """模拟视觉记忆系统"""
    
    def __init__(self):
        self.screenshots = {}
        self.scenario = "default"  # 当前测试场景
        self.step_index = 0
    
    def set_scenario(self, scenario: str):
        """设置测试场景"""
        self.scenario = scenario
        self.step_index = 0
    
    async def capture_fullscreen(self, task_id: str) -> Screenshot:
        """生成假的全屏截图"""
        # 根据场景生成不同的测试图
        generators = {
            "jianying_main": self._generate_jianying_main,
            "jianying_export": self._generate_jianying_export,
            "blender_viewport": self._generate_blender_viewport,
            "desktop": self._generate_desktop,
            "empty": self._generate_empty,
        }
        
        generator = generators.get(self.scenario, self._generate_desktop)
        image_data = generator()
        
        screenshot = Screenshot(
            id=f"mock_ss_{uuid.uuid4().hex[:8]}",
            task_id=task_id,
            image_data=image_data,
            width=1920,
            height=1080
        )
        
        self.screenshots[screenshot.id] = screenshot
        self.step_index += 1
        
        return screenshot
    
    async def capture_region(self, task_id: str, x: int, y: int, w: int, h: int) -> Screenshot:
        """生成假的区域截图"""
        if PIL_AVAILABLE:
            img = Image.new('RGB', (w, h), color=(100 + self.step_index * 20, 150, 200))
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            image_data = buffer.getvalue()
        else:
            image_data = b"mock_region_image"
        
        screenshot = Screenshot(
            id=f"mock_ss_{uuid.uuid4().hex[:8]}",
            task_id=task_id,
            image_data=image_data,
            width=w,
            height=h,
            region=(x, y, w, h)
        )
        
        self.screenshots[screenshot.id] = screenshot
        return screenshot
    
    def _generate_jianying_main(self) -> bytes:
        """生成剪映主界面模拟图"""
        if not PIL_AVAILABLE:
            return b"mock_jianying_main"
        
        img = Image.new('RGB', (1920, 1080), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        
        # 顶部工具栏
        draw.rectangle([0, 0, 1920, 60], fill=(50, 50, 50))
        draw.text((20, 20), "导入", fill=(255, 255, 255))
        draw.text((100, 20), "导出", fill=(255, 100, 50))
        
        # 左侧面板
        draw.rectangle([0, 60, 300, 1080], fill=(40, 40, 40))
        draw.text((20, 100), "素材库", fill=(200, 200, 200))
        
        # 预览窗口
        draw.rectangle([400, 100, 1400, 700], fill=(20, 20, 20), outline=(100, 100, 100))
        draw.text((800, 380), "预览窗口", fill=(100, 100, 100))
        
        # 时间轴
        draw.rectangle([300, 750, 1920, 1080], fill=(35, 35, 35))
        draw.text((1100, 900), "时间轴轨道", fill=(150, 150, 150))
        
        # 模拟按钮
        draw.rectangle([20, 150, 120, 190], fill=(60, 60, 60), outline=(100, 100, 100))
        draw.text((35, 160), "视频", fill=(255, 255, 255))
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def _generate_jianying_export(self) -> bytes:
        """生成剪映导出对话框"""
        if not PIL_AVAILABLE:
            return b"mock_jianying_export"
        
        img = Image.new('RGB', (1920, 1080), color=(30, 30, 30))
        draw = ImageDraw.Draw(img)
        
        # 导出对话框
        draw.rectangle([500, 200, 1420, 800], fill=(50, 50, 50), outline=(100, 100, 100))
        draw.text((900, 250), "导出设置", fill=(255, 255, 255))
        
        # 导出按钮
        draw.rectangle([1000, 700, 1200, 750], fill=(255, 100, 50))
        draw.text((1050, 715), "导出", fill=(255, 255, 255))
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def _generate_blender_viewport(self) -> bytes:
        """生成Blender视口"""
        if not PIL_AVAILABLE:
            return b"mock_blender_viewport"
        
        img = Image.new('RGB', (1920, 1080), color=(50, 50, 60))
        draw = ImageDraw.Draw(img)
        
        # 3D视口网格
        for i in range(0, 1920, 100):
            draw.line([(i, 0), (i, 1080)], fill=(60, 60, 70), width=1)
        for i in range(0, 1080, 100):
            draw.line([(0, i), (1920, i)], fill=(60, 60, 70), width=1)
        
        # 中心立方体
        draw.rectangle([800, 400, 1100, 700], fill=(100, 150, 200), outline=(150, 200, 255))
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def _generate_desktop(self) -> bytes:
        """生成桌面"""
        if not PIL_AVAILABLE:
            return b"mock_desktop"
        
        img = Image.new('RGB', (1920, 1080), color=(0, 120, 180))
        draw = ImageDraw.Draw(img)
        
        # 一些图标
        for i, name in enumerate(["剪映", "Blender", "Chrome", "文件夹"]):
            x = 50 + i * 150
            draw.rectangle([x, 50, x + 80, 130], fill=(255, 255, 255))
            draw.text((x + 10, 140), name, fill=(255, 255, 255))
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def _generate_empty(self) -> bytes:
        """生成空白图"""
        if not PIL_AVAILABLE:
            return b"mock_empty"
        
        img = Image.new('RGB', (1920, 1080), color=(50, 50, 50))
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def get_screenshot(self, screenshot_id: str) -> Optional[Screenshot]:
        return self.screenshots.get(screenshot_id)
