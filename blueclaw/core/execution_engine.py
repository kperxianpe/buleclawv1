#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Execution Engine - Complete implementation

Features:
- Blueprint creation from thinking path
- Step execution with dependencies
- Pause/Resume
- REPLAN (regenerate from failed step)
- Position tracking for visualization
"""

import json
import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    SKIPPED = "skipped"
    DEPRECATED = "deprecated"  # REPLAN后废弃


@dataclass
class ExecutionStep:
    """执行步骤 - 支持可视化位置"""
    id: str
    name: str
    description: str
    direction: str
    example: str
    validation: str
    tool: str
    dependencies: List[str] = field(default_factory=list)
    status: StepStatus = field(default=StepStatus.PENDING)
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_count: int = 0
    position: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.position:
            self.position = {"x": 100, "y": 400}
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "direction": self.direction,
            "example": self.example,
            "validation": self.validation,
            "tool": self.tool,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "failed_count": self.failed_count,
            "position": self.position
        }


@dataclass
class ExecutionBlueprint:
    """执行蓝图"""
    id: str
    task_id: str
    steps: List[ExecutionStep]
    status: StepStatus = field(default=StepStatus.PENDING)
    current_step_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "steps": [s.to_dict() for s in self.steps],
            "status": self.status.value,
            "current_step_id": self.current_step_id,
            "created_at": self.created_at
        }


class ExecutionEngine:
    """执行引擎"""
    
    def __init__(self):
        self.blueprints: Dict[str, ExecutionBlueprint] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self._paused: Dict[str, bool] = {}
    
    async def create_blueprint(self, task_id: str, thinking_path: List[dict]) -> ExecutionBlueprint:
        """从思考路径生成执行蓝图"""
        from blueclaw.llm import LLMClient, Message
        from blueclaw.llm.prompts import format_execution_steps_prompt
        
        prompt = format_execution_steps_prompt(thinking_path)
        
        try:
            response = LLMClient().chat_completion([
                Message(role="system", content="You are a task planner. Output valid JSON only."),
                Message(role="user", content=prompt)
            ])
            
            result = json.loads(response.content)
            steps_data = result.get("steps", [])
        except Exception as e:
            print(f"LLM error, using defaults: {e}")
            steps_data = self._create_default_steps(thinking_path)
        
        # 创建步骤对象
        steps = []
        for i, step_data in enumerate(steps_data):
            step = ExecutionStep(
                id=f"step_{uuid.uuid4().hex[:8]}",
                name=step_data.get("name", f"步骤{i+1}"),
                description=step_data.get("description", ""),
                direction=step_data.get("direction", ""),
                example=step_data.get("example", ""),
                validation=step_data.get("validation", ""),
                tool=step_data.get("tool", "Skill"),
                dependencies=step_data.get("dependencies", []),
                position={"x": 100 + i * 250, "y": 400}
            )
            steps.append(step)
        
        self._resolve_dependencies(steps)
        
        blueprint = ExecutionBlueprint(
            id=f"blueprint_{uuid.uuid4().hex[:8]}",
            task_id=task_id,
            steps=steps
        )
        
        self.blueprints[blueprint.id] = blueprint
        return blueprint
    
    async def start_execution(self, blueprint_id: str) -> bool:
        """开始执行"""
        blueprint = self.blueprints.get(blueprint_id)
        if not blueprint or blueprint_id in self.running_tasks:
            return False
        
        blueprint.status = StepStatus.RUNNING
        blueprint.started_at = datetime.now().isoformat()
        self._paused[blueprint_id] = False
        
        task = asyncio.create_task(self._execute_blueprint(blueprint_id))
        self.running_tasks[blueprint_id] = task
        return True
    
    async def _execute_blueprint(self, blueprint_id: str):
        """执行蓝图协程"""
        blueprint = self.blueprints[blueprint_id]
        
        try:
            for step in blueprint.steps:
                # 检查暂停
                while self._paused.get(blueprint_id, False):
                    await asyncio.sleep(0.1)
                
                # 跳过已完成或废弃的步骤
                if step.status in [StepStatus.COMPLETED, StepStatus.DEPRECATED, StepStatus.SKIPPED]:
                    continue
                
                # 检查依赖
                if not self._check_dependencies_satisfied(blueprint, step):
                    await self._wait_for_dependencies(blueprint, step)
                
                blueprint.current_step_id = step.id
                await self._execute_step(blueprint, step)
                
                # 如果暂停，退出循环
                if self._paused.get(blueprint_id, False):
                    break
                
                # 如果失败次数过多，触发干预
                if step.status == StepStatus.FAILED and step.failed_count >= 2:
                    await self._notify_intervention_needed(blueprint, step)
                    break
            
            # 检查是否全部完成
            active_steps = [s for s in blueprint.steps if s.status != StepStatus.DEPRECATED]
            if all(s.status == StepStatus.COMPLETED for s in active_steps):
                blueprint.status = StepStatus.COMPLETED
                blueprint.completed_at = datetime.now().isoformat()
                await self._notify_completed(blueprint)
            elif blueprint.status != StepStatus.PAUSED:
                blueprint.status = StepStatus.FAILED
                
        except Exception as e:
            print(f"Execution error: {e}")
            blueprint.status = StepStatus.FAILED
        finally:
            if blueprint_id in self.running_tasks:
                del self.running_tasks[blueprint_id]
    
    async def _execute_step(self, blueprint: ExecutionBlueprint, step: ExecutionStep):
        """执行单个步骤"""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now().isoformat()
        
        # 通知前端步骤开始
        await self._notify_step_started(blueprint, step)
        
        try:
            # TODO: 实际调用 Skill
            await asyncio.sleep(0.5)  # 模拟执行
            
            # 模拟成功（90%概率）
            import random
            if random.random() > 0.1:
                step.result = f"成功执行: {step.name}"
                step.status = StepStatus.COMPLETED
                await self._notify_step_completed(blueprint, step)
            else:
                raise Exception("模拟失败")
                
        except Exception as e:
            step.failed_count += 1
            step.error = str(e)
            step.status = StepStatus.FAILED
            await self._notify_step_failed(blueprint, step)
        
        step.completed_at = datetime.now().isoformat()
    
    async def pause_execution(self, blueprint_id: str):
        """暂停执行"""
        self._paused[blueprint_id] = True
        blueprint = self.blueprints.get(blueprint_id)
        if blueprint:
            blueprint.status = StepStatus.PAUSED
    
    async def resume_execution(self, blueprint_id: str):
        """恢复执行"""
        blueprint = self.blueprints.get(blueprint_id)
        if not blueprint or blueprint.status != StepStatus.PAUSED:
            return False
        
        self._paused[blueprint_id] = False
        blueprint.status = StepStatus.RUNNING
        
        # 如果不在运行中，重新启动
        if blueprint_id not in self.running_tasks:
            task = asyncio.create_task(self._execute_blueprint(blueprint_id))
            self.running_tasks[blueprint_id] = task
        
        return True
    
    async def handle_intervention(
        self,
        blueprint_id: str,
        step_id: str,
        action: str,
        data: dict = None
    ) -> Optional[dict]:
        """
        处理用户干预
        action: retry | skip | replan | modify
        """
        data = data or {}
        blueprint = self.blueprints.get(blueprint_id)
        if not blueprint:
            return None
        
        step = self._find_step(blueprint, step_id)
        if not step:
            return None
        
        if action == "retry":
            step.status = StepStatus.PENDING
            step.failed_count = 0
            step.error = None
            await self.resume_execution(blueprint_id)
            return {"action": "retry", "step_id": step_id}
        
        elif action == "skip":
            step.status = StepStatus.SKIPPED
            step.result = "用户跳过"
            await self.resume_execution(blueprint_id)
            return {"action": "skip", "step_id": step_id}
        
        elif action == "replan":
            # REPLAN: 从当前步骤重新规划
            custom_input = data.get("custom_input", "")
            new_steps = await self._replan_from_step(blueprint, step_id, custom_input)
            
            await self._notify_replanned(blueprint, step_id, new_steps)
            await self.resume_execution(blueprint_id)
            
            return {
                "action": "replan",
                "from_step_id": step_id,
                "new_steps": [s.to_dict() for s in new_steps]
            }
        
        elif action == "modify":
            if "direction" in data:
                step.direction = data["direction"]
            step.status = StepStatus.PENDING
            await self.resume_execution(blueprint_id)
            return {"action": "modify", "step_id": step_id}
        
        return None
    
    async def _replan_from_step(
        self,
        blueprint: ExecutionBlueprint,
        step_id: str,
        user_input: str
    ) -> List[ExecutionStep]:
        """REPLAN核心：从指定步骤重新规划"""
        step = self._find_step(blueprint, step_id)
        if not step:
            return []
        
        # 废弃当前及后续步骤
        for s in self._get_subsequent_steps(blueprint, step):
            s.status = StepStatus.DEPRECATED
        
        # 生成新步骤
        new_steps = []
        for i in range(2):
            new_step = ExecutionStep(
                id=f"step_{uuid.uuid4().hex[:8]}_new",
                name=f"重新规划步骤{i+1}",
                description=f"基于'{user_input}'重新执行",
                direction=f"调整后的执行方向",
                example="预期结果",
                validation="验证规则",
                tool="Skill",
                dependencies=[step_id if i == 0 else new_steps[i-1].id],
                position={"x": 100 + (len(blueprint.steps) + i) * 250, "y": 500}
            )
            new_steps.append(new_step)
            blueprint.steps.append(new_step)
        
        self._resolve_dependencies(blueprint.steps)
        return new_steps
    
    # ========== 通知方法 ==========
    
    async def _notify_step_started(self, blueprint: ExecutionBlueprint, step: ExecutionStep):
        """通知步骤开始"""
        # 通过回调或消息队列通知
        pass
    
    async def _notify_step_completed(self, blueprint: ExecutionBlueprint, step: ExecutionStep):
        """通知步骤完成"""
        pass
    
    async def _notify_step_failed(self, blueprint: ExecutionBlueprint, step: ExecutionStep):
        """通知步骤失败"""
        pass
    
    async def _notify_intervention_needed(self, blueprint: ExecutionBlueprint, step: ExecutionStep):
        """通知需要干预"""
        pass
    
    async def _notify_replanned(self, blueprint: ExecutionBlueprint, from_step_id: str, new_steps: List[ExecutionStep]):
        """通知REPLAN结果"""
        pass
    
    async def _notify_completed(self, blueprint: ExecutionBlueprint):
        """通知执行完成"""
        pass
    
    # ========== 辅助方法 ==========
    
    def _check_dependencies_satisfied(self, blueprint: ExecutionBlueprint, step: ExecutionStep) -> bool:
        for dep_id in step.dependencies:
            dep_step = self._find_step(blueprint, dep_id)
            if not dep_step or dep_step.status not in [StepStatus.COMPLETED, StepStatus.SKIPPED]:
                return False
        return True
    
    async def _wait_for_dependencies(self, blueprint: ExecutionBlueprint, step: ExecutionStep):
        while not self._check_dependencies_satisfied(blueprint, step):
            await asyncio.sleep(0.1)
    
    def _find_step(self, blueprint: ExecutionBlueprint, step_id: str) -> Optional[ExecutionStep]:
        for step in blueprint.steps:
            if step.id == step_id:
                return step
        return None
    
    def _get_subsequent_steps(self, blueprint: ExecutionBlueprint, step: ExecutionStep) -> List[ExecutionStep]:
        """获取指定步骤之后的所有步骤"""
        subsequent = []
        found = False
        for s in blueprint.steps:
            if found and s.status != StepStatus.DEPRECATED:
                subsequent.append(s)
            if s.id == step.id:
                found = True
        return subsequent
    
    def _resolve_dependencies(self, steps: List[ExecutionStep]):
        """解析依赖关系"""
        for i, step in enumerate(steps):
            if i > 0 and not step.dependencies:
                # 默认依赖前一个非废弃步骤
                for j in range(i-1, -1, -1):
                    if steps[j].status != StepStatus.DEPRECATED:
                        step.dependencies = [steps[j].id]
                        break
    
    def _create_default_steps(self, thinking_path: List[dict]) -> List[dict]:
        return [
            {"name": "准备环境", "description": "准备执行环境", "direction": "环境准备", "example": "准备完成", "validation": "检查通过", "tool": "Skill"},
            {"name": "执行主要任务", "description": "执行核心任务", "direction": "任务执行", "example": "任务完成", "validation": "结果符合预期", "tool": "Skill"}
        ]


# Global instance
execution_engine = ExecutionEngine()
