#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Blueclaw v1.0 - Week 15 Implementation

分层画布架构 + LLM 思考引擎 + 状态持久化
"""

from .canvas.layered_canvas import LayeredCanvasSystem, ThinkingCanvas, ExecutionCanvas
from .canvas.position_awareness import (
    CanvasPositionAwareness, 
    CanvasElementLocator,
    ElementInfo,
    LayoutSnapshot
)
from .core.llm_thinking_engine import LLMThinkingEngine, create_llm_thinking_engine
from .widgets.chat_panel import ChatPanel
from .main_window import BlueclawV1MainWindow

__version__ = "1.0.0-week15"

__all__ = [
    # Canvas
    'LayeredCanvasSystem',
    'ThinkingCanvas',
    'ExecutionCanvas',
    'CanvasPositionAwareness',
    'CanvasElementLocator',
    'ElementInfo',
    'LayoutSnapshot',
    
    # Core
    'LLMThinkingEngine',
    'create_llm_thinking_engine',
    
    # Widgets
    'ChatPanel',
    
    # Main
    'BlueclawV1MainWindow',
]
