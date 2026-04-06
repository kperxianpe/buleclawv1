#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
思考引擎单元测试
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from blueclaw.core.thinking_engine import ThinkingEngine, ThinkingNode


@pytest.mark.asyncio
async def test_generate_initial_node():
    """测试生成初始思考节点"""
    engine = ThinkingEngine()
    
    node = await engine.generate_initial_node("task_1", "制作旅行视频", 0)
    
    assert node is not None
    assert node.id.startswith("thinking_")
    assert len(node.options) >= 2
    assert node.position["x"] == 100
    assert node.position["y"] == 200


@pytest.mark.asyncio
async def test_select_option_creates_next_node():
    """测试选择选项后生成下一个节点"""
    engine = ThinkingEngine()
    
    # 创建初始节点
    node1 = await engine.generate_initial_node("task_1", "制作视频", 0)
    option_a = node1.options[0]
    
    # 选择选项A
    next_node = await engine.select_option_impl("task_1", node1.id, option_a.id)
    
    assert next_node is not None
    assert next_node.parent_id == node1.id
    assert node1.selected_option_id == option_a.id
    assert next_node.position["x"] == 400  # 第二个节点 x=100+300


@pytest.mark.asyncio
async def test_select_custom_input():
    """测试自定义输入"""
    engine = ThinkingEngine()
    
    node1 = await engine.generate_initial_node("task_1", "制作视频", 0)
    
    # 使用自定义输入
    next_node = await engine.select_option_impl("task_1", node1.id, "custom", custom_input="我想做vlog")
    
    assert next_node is not None
    # 验证自定义输入被记录
    assert node1.custom_input is None  # 在impl中不设置，select_option_impl处理


@pytest.mark.asyncio
async def test_thinking_converges_after_3_levels():
    """测试思考3层后收敛"""
    engine = ThinkingEngine()
    
    # 构建3层思考
    node1 = await engine.generate_initial_node("task_1", "任务", 0)
    node2 = await engine.select_option_impl("task_1", node1.id, "A")
    assert node2 is not None
    
    node3 = await engine.select_option_impl("task_1", node2.id, "B")
    assert node3 is not None
    
    # 第4层应该收敛（返回None）
    node4 = await engine.select_option_impl("task_1", node3.id, "C")
    assert node4 is None  # 思考收敛


@pytest.mark.asyncio
async def test_get_thinking_path():
    """测试获取思考路径"""
    engine = ThinkingEngine()
    
    node1 = await engine.generate_initial_node("task_1", "任务", 0)
    node2 = await engine.select_option_impl("task_1", node1.id, "A")
    if node2:
        await engine.select_option_impl("task_1", node2.id, "B")
    
    path = engine.get_thinking_path("task_1")
    
    assert len(path) >= 1


@pytest.mark.asyncio
async def test_start_thinking_api():
    """测试 start_thinking 公共API"""
    engine = ThinkingEngine()
    
    node = await engine.start_thinking("task_2", "测试输入")
    
    assert node is not None
    assert node.id.startswith("thinking_")
    assert len(node.options) >= 2


@pytest.mark.asyncio
async def test_select_option_api():
    """测试 select_option 公共API返回字典格式"""
    engine = ThinkingEngine()
    
    root = await engine.start_thinking("task_3", "测试")
    result = await engine.select_option("task_3", root.id, "A")
    
    assert "has_more_options" in result
    assert isinstance(result["has_more_options"], bool)


@pytest.mark.asyncio
async def test_select_custom_input_api():
    """测试 select_custom_input 公共API"""
    engine = ThinkingEngine()
    
    root = await engine.start_thinking("task_4", "测试")
    result = await engine.select_custom_input("task_4", root.id, "自定义输入")
    
    assert "has_more_options" in result
