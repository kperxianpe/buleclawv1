# -*- coding: utf-8 -*-
"""
engine_facade.py - Blueclaw 引擎外观层

统一引擎外观 - 隐藏内部实现，暴露稳定接口
- V1: 包装 DynamicThinkingEngine + ExecutionBlueprintSystem
- V2: 可以无缝切换到 CanvasMind 内核
- V3: 可以接入 Adapter 系统

设计原则:
- 接口稳定，内部实现可演进
- 所有方法返回标准数据结构
- 与具体引擎实现解耦
"""

from __future__ import annotations

import uuid
import time
import asyncio
from typing import Optional, List, Dict, Any, Callable, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum

# 导入现有引擎
from ..core.dynamic_thinking_engine import (
    DynamicThinkingEngine, 
    ThinkingResult, 
    ThinkingResultType,
    ThinkingOption,
    ClarificationQuestion,
    create_dynamic_thinking_engine
)
from ..core.execution_blueprint import (
    ExecutionBlueprintSystem, 
    ExecutionStep,
    StepStatus,
    ExecutionResult,
    create_execution_blueprint_system
)

# 导入消息协议
from .message_protocol import (
    ThinkingNodeData, 
    ThinkingOptionData, 
    ExecutionStepData,
    InterventionActionData,
    MessageFactory,
    MessageType,
    NodeStatus,
    Phase
)


# ==================== 外观层数据模型 ====================

@dataclass
class ReplanResult:
    """重新规划结果"""
    success: bool
    new_steps: Optional[List[Dict[str, Any]]] = None
    message: str = ""
    stopped: bool = False


@dataclass
class ThinkingResultData:
    """思考结果数据 - 用于前端"""
    result_type: str
    confidence: float
    direct_answer: Optional[str] = None
    question: Optional[ThinkingNodeData] = None
    options: Optional[List[ThinkingOptionData]] = None
    execution_preview: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_engine_result(cls, result: ThinkingResult, node_id: str = None) -> "ThinkingResultData":
        """从引擎结果创建"""
        node_id = node_id or f"thinking_{int(time.time() * 1000)}"
        
        data = cls(
            result_type=result.result_type.value,
            confidence=result.confidence
        )
        
        if result.direct_answer:
            data.direct_answer = result.direct_answer
        
        if result.clarification_question:
            q = result.clarification_question
            data.question = ThinkingNodeData(
                id=node_id,
                question=q.text,
                options=[
                    ThinkingOptionData(
                        id=opt["id"],
                        label=opt["label"],
                        description=opt.get("description", ""),
                        confidence=0.8
                    )
                    for opt in (q.options or [])
                ] if q.options else [],
                status=NodeStatus.PENDING
            )
        
        if result.options:
            data.options = [
                ThinkingOptionData(
                    id=opt.id,
                    label=opt.label,
                    description=opt.description,
                    confidence=opt.confidence,
                    is_default=opt.is_default
                )
                for opt in result.options
            ]
        
        if result.execution_preview:
            preview = result.execution_preview
            data.execution_preview = {
                "task_type": preview.task_type,
                "complexity": preview.complexity,
                "steps": preview.steps,
                "estimated_time": preview.estimated_time,
                "risks": preview.risks
            }
        
        return data


@dataclass
class EngineState:
    """引擎状态"""
    phase: Phase = Phase.IDLE
    current_node_id: Optional[str] = None
    current_step_id: Optional[str] = None
    progress: int = 0
    status_message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value if isinstance(self.phase, Enum) else self.phase,
            "current_node_id": self.current_node_id,
            "current_step_id": self.current_step_id,
            "progress": self.progress,
            "status_message": self.status_message
        }


# ==================== 事件回调类型 ====================

ThinkingNodeCreatedCallback = Callable[[ThinkingNodeData], None]
OptionSelectedCallback = Callable[[str, str], None]  # node_id, option_id
BlueprintLoadedCallback = Callable[[List[ExecutionStepData]], None]
StepStatusChangedCallback = Callable[[str, str, int], None]  # step_id, status, index
ExecutionCompletedCallback = Callable[[bool, str], None]  # success, summary
InterventionNeededCallback = Callable[[str, str, List[InterventionActionData]], None]  # step_id, reason, actions
StateChangedCallback = Callable[[EngineState], None]
MessageEmittedCallback = Callable[[str], None]


# ==================== 引擎外观 ====================

class BlueclawEngineFacade:
    """
    Blueclaw 统一引擎外观
    
    这是与前端交互的唯一接口，隐藏了内部引擎实现。
    无论内部使用 V1 动态引擎、V2 CanvasMind 还是 V3 Adapter 系统，
    此接口保持稳定。
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        
        # 内部引擎实例
        # V1: 使用 DynamicThinkingEngine + ExecutionBlueprintSystem
        self._thinking_engine: DynamicThinkingEngine = create_dynamic_thinking_engine()
        self._execution_engine: ExecutionBlueprintSystem = create_execution_blueprint_system()
        
        # 未来可以通过配置替换引擎
        # self._thinking_engine = get_configured_thinking_engine()
        # self._execution_engine = get_configured_execution_engine()
        
        # 当前状态
        self._state = EngineState()
        self._current_thinking_node: Optional[ThinkingNodeData] = None
        self._current_question: Optional[ClarificationQuestion] = None
        self._execution_steps: Dict[str, ExecutionStepData] = {}
        
        # 回调函数
        self._on_thinking_node_created: Optional[ThinkingNodeCreatedCallback] = None
        self._on_option_selected: Optional[OptionSelectedCallback] = None
        self._on_blueprint_loaded: Optional[BlueprintLoadedCallback] = None
        self._on_step_status_changed: Optional[StepStatusChangedCallback] = None
        self._on_execution_completed: Optional[ExecutionCompletedCallback] = None
        self._on_intervention_needed: Optional[InterventionNeededCallback] = None
        self._on_state_changed: Optional[StateChangedCallback] = None
        self._on_message: Optional[MessageEmittedCallback] = None
        
        # 绑定内部引擎回调
        self._bind_execution_callbacks()
        
        self._log(f"[INIT] EngineFacade initialized (session: {self.session_id})")
    
    # ============ 回调设置 ============
    
    def set_callbacks(
        self,
        on_thinking_node_created: Optional[ThinkingNodeCreatedCallback] = None,
        on_option_selected: Optional[OptionSelectedCallback] = None,
        on_blueprint_loaded: Optional[BlueprintLoadedCallback] = None,
        on_step_status_changed: Optional[StepStatusChangedCallback] = None,
        on_execution_completed: Optional[ExecutionCompletedCallback] = None,
        on_intervention_needed: Optional[InterventionNeededCallback] = None,
        state_changed: Optional[StateChangedCallback] = None,
        message: Optional[MessageEmittedCallback] = None
    ):
        """设置回调函数"""
        self._on_thinking_node_created = on_thinking_node_created
        self._on_option_selected = on_option_selected
        self._on_blueprint_loaded = on_blueprint_loaded
        self._on_step_status_changed = on_step_status_changed
        self._on_execution_completed = on_execution_completed
        self._on_intervention_needed = on_intervention_needed
        self._on_state_changed = state_changed
        self._on_message = message
    
    def _bind_execution_callbacks(self):
        """绑定执行引擎回调"""
        self._execution_engine.on_blueprint_loaded = self._on_execution_blueprint_loaded
        self._execution_engine.on_step_start = self._on_execution_step_start
        self._execution_engine.on_step_complete = self._on_execution_step_complete
        self._execution_engine.on_execution_complete = self._on_execution_result
        self._execution_engine.on_intervention_needed = self._on_execution_intervention
    
    # ============ 状态管理 ============
    
    def _update_state(self, **kwargs):
        """更新状态"""
        for key, value in kwargs.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
        
        if self._on_state_changed:
            self._on_state_changed(self._state)
    
    def _log(self, message: str):
        """记录日志"""
        if self._on_message:
            self._on_message(message)
    
    @property
    def state(self) -> EngineState:
        """获取当前状态"""
        return self._state
    
    # ============ 核心接口 ============
    
    async def process(self, user_input: str, context: Optional[Dict] = None) -> ThinkingResultData:
        """
        统一处理入口 - 接口稳定
        
        处理用户输入，返回思考结果
        """
        self._log(f"[PROCESS] Input: {user_input[:50]}...")
        self._update_state(phase=Phase.THINKING, status_message="AI思考中...")
        
        # 调用思考引擎
        result = self._thinking_engine.process(user_input, context)
        
        # 转换为标准数据格式
        node_id = f"thinking_{int(time.time() * 1000)}"
        result_data = ThinkingResultData.from_engine_result(result, node_id)
        
        # 处理不同类型的结果
        if result_data.question:
            # 有澄清问题
            self._current_thinking_node = result_data.question
            self._current_question = result.clarification_question
            self._update_state(
                current_node_id=node_id,
                status_message="需要更多信息"
            )
            
            if self._on_thinking_node_created:
                self._on_thinking_node_created(result_data.question)
                
        elif result_data.options:
            # 有选项
            self._current_thinking_node = ThinkingNodeData(
                id=node_id,
                question="请选择执行方案",
                options=result_data.options,
                status=NodeStatus.PENDING
            )
            self._update_state(
                current_node_id=node_id,
                status_message="等待选择"
            )
            
            if self._on_thinking_node_created:
                self._on_thinking_node_created(self._current_thinking_node)
        
        elif result_data.execution_preview:
            # 直接生成执行预览
            self._update_state(status_message="生成执行计划")
            await self._load_execution_blueprint(result_data.execution_preview["steps"])
        
        elif result_data.direct_answer:
            # 直接回答
            self._update_state(phase=Phase.COMPLETED, status_message="完成")
        
        return result_data
    
    async def select_option(self, node_id: str, option_id: str) -> ThinkingResultData:
        """
        选择选项 - 接口稳定
        
        用户选择了某个选项后的处理
        """
        self._log(f"[SELECT] Node: {node_id}, Option: {option_id}")
        
        # 找到对应的选项
        if self._current_thinking_node and self._current_thinking_node.id == node_id:
            self._current_thinking_node.selected_option = option_id
            self._current_thinking_node.status = NodeStatus.SELECTED
        
        if self._on_option_selected:
            self._on_option_selected(node_id, option_id)
        
        # 查找原始选项对象
        selected_option = None
        if self._thinking_engine.current_context.get('selected_option'):
            # 从引擎上下文获取
            for opt in self._thinking_engine.current_context.get('options', []):
                if isinstance(opt, ThinkingOption) and opt.id == option_id:
                    selected_option = opt
                    break
        
        # 调用引擎继续处理
        if selected_option:
            result = self._thinking_engine.continue_with_option(option_id, selected_option)
        else:
            # 创建临时选项
            temp_option = ThinkingOption(
                id=option_id,
                label=option_id,
                description="",
                confidence=0.8
            )
            result = self._thinking_engine.continue_with_option(option_id, temp_option)
        
        return await self._handle_thinking_result(result)
    
    async def provide_clarification(self, node_id: str, answer: str) -> ThinkingResultData:
        """
        提供澄清回答
        """
        self._log(f"[CLARIFY] Node: {node_id}, Answer: {answer}")
        
        if self._current_question:
            result = self._thinking_engine.continue_with_clarification(answer, self._current_question)
            return await self._handle_thinking_result(result)
        else:
            # 没有待回答的问题，重新处理
            return await self.process(answer)
    
    async def _handle_thinking_result(self, result: ThinkingResult) -> ThinkingResultData:
        """处理思考结果"""
        node_id = f"thinking_{int(time.time() * 1000)}"
        result_data = ThinkingResultData.from_engine_result(result, node_id)
        
        if result_data.execution_preview:
            await self._load_execution_blueprint(result_data.execution_preview["steps"])
        
        return result_data
    
    async def _load_execution_blueprint(self, steps_data: List[Dict[str, Any]]):
        """加载执行蓝图"""
        self._update_state(phase=Phase.EXECUTING, status_message="加载执行蓝图")
        
        # 转换为标准格式
        execution_steps = []
        for i, step_data in enumerate(steps_data):
            step = ExecutionStepData(
                id=step_data.get("id", f"step_{i}"),
                name=step_data.get("name", f"步骤 {i+1}"),
                description=step_data.get("description", ""),
                dependencies=step_data.get("dependencies", []),
                status=NodeStatus.PENDING
            )
            execution_steps.append(step)
            self._execution_steps[step.id] = step
        
        # 加载到执行引擎
        self._execution_engine.load_blueprint([
            {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "dependencies": step.dependencies
            }
            for step in execution_steps
        ])
        
        if self._on_blueprint_loaded:
            self._on_blueprint_loaded(execution_steps)
        
        # 开始执行
        asyncio.create_task(self._execute_all())
    
    async def _execute_all(self):
        """执行所有步骤"""
        result = await self._execution_engine.execute_all()
        self._on_execution_result(result)
    
    # ============ 执行控制 ============
    
    def pause_execution(self):
        """暂停执行"""
        self._log("[CONTROL] Pausing execution")
        self._execution_engine.pause_execution()
        self._update_state(status_message="已暂停")
    
    def resume_execution(self):
        """恢复执行"""
        self._log("[CONTROL] Resuming execution")
        self._execution_engine.resume_execution()
        self._update_state(status_message="执行中...")
        asyncio.create_task(self._execution_engine.execute_from_current())
    
    def skip_current_step(self):
        """跳过当前步骤"""
        self._log("[CONTROL] Skipping current step")
        self._execution_engine.skip_current_step()
    
    async def intervene(self, step_id: str, action_type: str, custom_input: Optional[str] = None) -> ReplanResult:
        """
        干预 - 接口稳定，内部实现可演进
        
        现在: 简单的重新规划
        未来: 可以接入 V3 的 REPLAN 协议
        """
        self._log(f"[INTERVENTION] Step: {step_id}, Action: {action_type}")
        self._update_state(phase=Phase.INTERVENING, status_message="处理干预...")
        
        # 找到步骤索引
        step_index = -1
        if self._execution_engine.blueprint:
            for i, step in enumerate(self._execution_engine.blueprint):
                if step.id == step_id:
                    step_index = i
                    break
        
        if action_type == "replan":
            # 触发重新思考
            context = f"执行到步骤 '{step_id}' 需要重新规划"
            if custom_input:
                context += f": {custom_input}"
            
            result = self._thinking_engine.process(context)
            
            if result.execution_preview:
                new_steps = result.execution_preview.steps
                self._execution_engine.replan_from_step(step_index, new_steps)
                
                # 转换为标准格式
                execution_steps = []
                for i, step_data in enumerate(new_steps):
                    step = ExecutionStepData(
                        id=step_data.get("id", f"step_{step_index + i}"),
                        name=step_data.get("name", f"步骤 {step_index + i + 1}"),
                        description=step_data.get("description", ""),
                        status=NodeStatus.PENDING
                    )
                    execution_steps.append(step)
                
                if self._on_blueprint_loaded:
                    self._on_blueprint_loaded(execution_steps)
                
                self._update_state(phase=Phase.EXECUTING, status_message="重新规划完成")
                
                # 继续执行
                asyncio.create_task(self._execution_engine.execute_from_current())
                
                return ReplanResult(
                    success=True,
                    new_steps=new_steps,
                    message="重新规划完成"
                )
            
            return ReplanResult(success=False, message="重新规划失败")
        
        elif action_type == "skip":
            self._execution_engine.skip_current_step()
            asyncio.create_task(self._execution_engine.execute_from_current())
            return ReplanResult(success=True, message="已跳过")
        
        elif action_type == "stop":
            self._execution_engine.pause_execution()
            self._update_state(phase=Phase.IDLE, status_message="已停止")
            return ReplanResult(success=True, stopped=True, message="已停止")
        
        elif action_type == "retry":
            asyncio.create_task(self._execution_engine.resume_after_intervention())
            return ReplanResult(success=True, message="重试中...")
        
        return ReplanResult(success=False, message=f"未知的干预类型: {action_type}")
    
    # ============ 执行引擎回调 ============
    
    def _on_execution_blueprint_loaded(self, steps: List[ExecutionStep]):
        """蓝图加载回调"""
        self._log(f"[BLUEPRINT] Loaded {len(steps)} steps")
    
    def _on_execution_step_start(self, step: ExecutionStep):
        """步骤开始回调"""
        self._log(f"[STEP] Starting: {step.name}")
        
        # 更新步骤状态
        if step.id in self._execution_steps:
            self._execution_steps[step.id].status = NodeStatus.RUNNING
        
        # 找到索引
        index = -1
        if self._execution_engine.blueprint:
            for i, s in enumerate(self._execution_engine.blueprint):
                if s.id == step.id:
                    index = i
                    break
        
        self._update_state(
            current_step_id=step.id,
            status_message=f"执行: {step.name}"
        )
        
        if self._on_step_status_changed:
            self._on_step_status_changed(step.id, NodeStatus.RUNNING, index)
    
    def _on_execution_step_complete(self, step: ExecutionStep, success: bool):
        """步骤完成回调"""
        status = NodeStatus.COMPLETED if success else NodeStatus.FAILED
        self._log(f"[STEP] Completed: {step.name} ({status.value})")
        
        # 更新步骤状态
        if step.id in self._execution_steps:
            self._execution_steps[step.id].status = status
            self._execution_steps[step.id].result = step.result
            self._execution_steps[step.id].error = step.error
            self._execution_steps[step.id].duration_ms = step.get_duration_ms()
        
        # 找到索引
        index = -1
        if self._execution_engine.blueprint:
            for i, s in enumerate(self._execution_engine.blueprint):
                if s.id == step.id:
                    index = i
                    break
        
        # 更新进度
        if self._execution_engine.blueprint:
            completed = sum(1 for s in self._execution_engine.blueprint 
                          if s.status == StepStatus.COMPLETED)
            total = len(self._execution_engine.blueprint)
            progress = int((completed / total) * 100)
            self._update_state(progress=progress)
        
        if self._on_step_status_changed:
            self._on_step_status_changed(step.id, status, index)
    
    def _on_execution_result(self, result: ExecutionResult):
        """执行结果回调"""
        self._log(f"[DONE] Execution completed: {result.summary}")
        self._update_state(
            phase=Phase.COMPLETED,
            status_message=result.summary,
            progress=100
        )
        
        if self._on_execution_completed:
            self._on_execution_completed(result.success, result.summary)
    
    def _on_execution_intervention(self, intervention):
        """需要干预回调"""
        self._log(f"[INTERVENTION] Needed for: {intervention.step_name}")
        
        actions = [
            InterventionActionData("retry", "重试", "重新执行当前步骤"),
            InterventionActionData("skip", "跳过", "跳过当前步骤继续"),
            InterventionActionData("replan", "重新规划", "回退到思考阶段重新规划"),
            InterventionActionData("stop", "停止", "停止执行")
        ]
        
        self._update_state(
            phase=Phase.INTERVENING,
            status_message=f"需要干预: {intervention.step_name}"
        )
        
        if self._on_intervention_needed:
            self._on_intervention_needed(intervention.step_id, intervention.reason, actions)
    
    # ============ 查询接口 ============
    
    def get_progress(self) -> Dict[str, Any]:
        """获取执行进度"""
        return self._execution_engine.get_progress()
    
    def get_execution_steps(self) -> List[ExecutionStepData]:
        """获取执行步骤"""
        return list(self._execution_steps.values())
    
    def get_current_step(self) -> Optional[ExecutionStepData]:
        """获取当前步骤"""
        current = self._execution_engine.get_current_step()
        if current:
            return self._execution_steps.get(current.id)
        return None


def create_engine_facade(session_id: Optional[str] = None) -> BlueclawEngineFacade:
    """创建引擎外观实例"""
    return BlueclawEngineFacade(session_id)
