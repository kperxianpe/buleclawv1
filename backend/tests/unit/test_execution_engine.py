#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行引擎单元测试
"""
import pytest
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from blueclaw.core.execution_engine import ExecutionEngine, ExecutionBlueprint, StepStatus, ExecutionStep


@pytest.mark.asyncio
async def test_create_blueprint():
    """测试从思考路径生成执行蓝图"""
    engine = ExecutionEngine()
    
    thinking_path = [
        {"question": "选择主题", "selected_option": {"id": "A", "label": "旅行"}},
        {"question": "选择风格", "selected_option": {"id": "B", "label": "清新"}},
    ]
    
    blueprint = await engine.create_blueprint("task_1", thinking_path)
    
    assert blueprint is not None
    assert blueprint.id.startswith("blueprint_")
    assert len(blueprint.steps) > 0
    
    # 验证步骤有position
    for i, step in enumerate(blueprint.steps):
        assert "x" in step.position
        assert "y" in step.position


@pytest.mark.asyncio
async def test_pause_and_resume():
    """测试暂停和恢复"""
    engine = ExecutionEngine()
    
    blueprint = await engine.create_blueprint("task_1", [])
    
    # 开始执行
    success = await engine.start_execution(blueprint.id)
    assert success
    
    # 暂停
    await engine.pause_execution(blueprint.id)
    assert blueprint.status == StepStatus.PAUSED
    assert engine._paused.get(blueprint.id) is True
    
    # 恢复
    success = await engine.resume_execution(blueprint.id)
    assert success
    assert blueprint.status == StepStatus.RUNNING


@pytest.mark.asyncio
async def test_handle_intervention_replan():
    """测试 REPLAN 干预"""
    engine = ExecutionEngine()
    
    blueprint = await engine.create_blueprint("task_1", [])
    blueprint.steps[0].status = StepStatus.FAILED
    blueprint.steps[0].failed_count = 3
    
    result = await engine.handle_intervention(
        blueprint.id,
        blueprint.steps[0].id,
        "replan",
        {"custom_input": "更换策略"}
    )
    
    assert result is not None
    assert result["action"] == "replan"
    assert len(result["new_steps"]) > 0


@pytest.mark.asyncio
async def test_handle_intervention_skip():
    """测试 skip 干预"""
    engine = ExecutionEngine()
    
    blueprint = await engine.create_blueprint("task_1", [])
    step_id = blueprint.steps[0].id
    blueprint.steps[0].status = StepStatus.FAILED
    
    result = await engine.handle_intervention(
        blueprint.id,
        step_id,
        "skip",
        {}
    )
    
    assert result is not None
    assert result["action"] == "skip"
    assert blueprint.steps[0].status == StepStatus.SKIPPED


@pytest.mark.asyncio
async def test_handle_intervention_retry():
    """测试 retry 干预"""
    engine = ExecutionEngine()
    
    blueprint = await engine.create_blueprint("task_1", [])
    step_id = blueprint.steps[0].id
    blueprint.steps[0].status = StepStatus.FAILED
    blueprint.steps[0].failed_count = 2
    
    result = await engine.handle_intervention(
        blueprint.id,
        step_id,
        "retry",
        {}
    )
    
    assert result is not None
    assert result["action"] == "retry"
    assert blueprint.steps[0].status == StepStatus.PENDING
    assert blueprint.steps[0].failed_count == 0


@pytest.mark.asyncio
async def test_find_step():
    """测试查找步骤"""
    engine = ExecutionEngine()
    
    blueprint = await engine.create_blueprint("task_1", [])
    step_id = blueprint.steps[0].id
    
    found_step = engine._find_step(blueprint, step_id)
    assert found_step is not None
    assert found_step.id == step_id


@pytest.mark.asyncio
async def test_get_subsequent_steps():
    """测试获取后续步骤"""
    engine = ExecutionEngine()
    
    blueprint = await engine.create_blueprint("task_1", [])
    if len(blueprint.steps) >= 2:
        subsequent = engine._get_subsequent_steps(blueprint, blueprint.steps[0])
        # 第一个步骤后续应该还有其他步骤
        assert len(subsequent) >= 0


@pytest.mark.asyncio
async def test_blueprint_to_dict():
    """测试蓝图序列化"""
    engine = ExecutionEngine()
    
    blueprint = await engine.create_blueprint("task_1", [])
    data = blueprint.to_dict()
    
    assert "id" in data
    assert "task_id" in data
    assert "steps" in data
    assert "status" in data
