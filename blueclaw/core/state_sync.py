#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
State Sync Manager - WebSocket message broadcasting

Handles all real-time state updates to frontend
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime


class StateSyncManager:
    """状态同步管理器"""
    
    def __init__(self):
        self.websocket_server = None
    
    def set_websocket_server(self, server):
        self.websocket_server = server
    
    async def broadcast_to_task(self, task_id: str, message: dict):
        """广播消息到任务的所有连接"""
        if self.websocket_server:
            await self.websocket_server.broadcast_to_task(task_id, message)
    
    # ========== Thinking Phase ==========
    
    async def push_thinking_node_created(self, task_id: str, node, is_root: bool = False):
        """推送思考节点创建"""
        await self.broadcast_to_task(task_id, {
            "type": "thinking.node_created" if is_root else "thinking.node_selected",
            "payload": {
                "node": node.to_dict() if hasattr(node, 'to_dict') else node,
                "options": [
                    {
                        "id": opt.id if hasattr(opt, 'id') else opt.get('id'),
                        "label": opt.label if hasattr(opt, 'label') else opt.get('label'),
                        "description": opt.description if hasattr(opt, 'description') else opt.get('description'),
                        "confidence": opt.confidence if hasattr(opt, 'confidence') else opt.get('confidence'),
                        "is_default": opt.recommended if hasattr(opt, 'recommended') else opt.get('recommended', False)
                    } for opt in (node.options if hasattr(node, 'options') else node.get('options', []))
                ],
                "allow_custom": node.allow_custom if hasattr(node, 'allow_custom') else node.get('allow_custom', True),
                "previous_node_id": node.parent_id if hasattr(node, 'parent_id') else node.get('parent_id') if not is_root else None
            },
            "timestamp": self._timestamp(),
            "message_id": self._message_id()
        })
    
    async def push_thinking_completed(self, task_id: str, final_path: List[dict]):
        """推送思考完成"""
        await self.broadcast_to_task(task_id, {
            "type": "thinking.completed",
            "payload": {
                "final_path": final_path
            },
            "timestamp": self._timestamp(),
            "message_id": self._message_id()
        })
    
    # ========== Execution Phase ==========
    
    async def push_execution_blueprint_loaded(self, task_id: str, blueprint):
        """推送执行蓝图加载"""
        steps_data = []
        for step in (blueprint.steps if hasattr(blueprint, 'steps') else blueprint.get('steps', [])):
            steps_data.append({
                "id": step.id if hasattr(step, 'id') else step.get('id'),
                "name": step.name if hasattr(step, 'name') else step.get('name'),
                "description": step.direction if hasattr(step, 'direction') else step.get('direction', ''),
                "status": step.status.value if hasattr(step, 'status') else step.get('status', 'pending'),
                "dependencies": step.dependencies if hasattr(step, 'dependencies') else step.get('dependencies', []),
                "position": step.position if hasattr(step, 'position') else step.get('position', {}),
                "tool": step.tool if hasattr(step, 'tool') else step.get('tool', 'Skill')
            })
        
        await self.broadcast_to_task(task_id, {
            "type": "execution.blueprint_loaded",
            "payload": {
                "blueprint_id": blueprint.id if hasattr(blueprint, 'id') else blueprint.get('id'),
                "steps": steps_data
            },
            "timestamp": self._timestamp(),
            "message_id": self._message_id()
        })
    
    async def push_execution_step_started(self, task_id: str, step):
        """推送步骤开始"""
        await self.broadcast_to_task(task_id, {
            "type": "execution.step_started",
            "payload": {
                "step_id": step.id if hasattr(step, 'id') else step.get('id'),
                "step_name": step.name if hasattr(step, 'name') else step.get('name'),
                "status": "running",
                "start_time": step.started_at if hasattr(step, 'started_at') else step.get('started_at')
            },
            "timestamp": self._timestamp(),
            "message_id": self._message_id()
        })
    
    async def push_execution_step_completed(self, task_id: str, step):
        """推送步骤完成"""
        await self.broadcast_to_task(task_id, {
            "type": "execution.step_completed",
            "payload": {
                "step_id": step.id if hasattr(step, 'id') else step.get('id'),
                "status": "completed",
                "result": step.result if hasattr(step, 'result') else step.get('result'),
                "duration_ms": self._calculate_duration(step)
            },
            "timestamp": self._timestamp(),
            "message_id": self._message_id()
        })
    
    async def push_execution_step_failed(self, task_id: str, step):
        """推送步骤失败"""
        failed_count = step.failed_count if hasattr(step, 'failed_count') else step.get('failed_count', 0)
        await self.broadcast_to_task(task_id, {
            "type": "execution.step_failed",
            "payload": {
                "step_id": step.id if hasattr(step, 'id') else step.get('id'),
                "status": "failed",
                "error": step.error if hasattr(step, 'error') else step.get('error'),
                "can_retry": failed_count < 3
            },
            "timestamp": self._timestamp(),
            "message_id": self._message_id()
        })
    
    async def push_execution_intervention_needed(self, task_id: str, step, blueprint):
        """推送需要干预"""
        await self.broadcast_to_task(task_id, {
            "type": "execution.intervention_needed",
            "payload": {
                "step_id": step.id if hasattr(step, 'id') else step.get('id'),
                "step_name": step.name if hasattr(step, 'name') else step.get('name'),
                "reason": step.error if hasattr(step, 'error') else step.get('error', '执行失败'),
                "suggested_actions": [
                    {"id": "replan", "label": "重新规划", "description": "更换策略重新执行"},
                    {"id": "skip", "label": "跳过此步", "description": "继续后续步骤"},
                    {"id": "retry", "label": "重试", "description": "再次尝试执行"},
                    {"id": "custom", "label": "自定义方案", "description": "输入您的偏好"}
                ]
            },
            "timestamp": self._timestamp(),
            "message_id": self._message_id()
        })
    
    async def push_execution_replanned(self, task_id: str, from_step_id: str, abandoned_steps: List[str], new_steps: List[dict]):
        """推送 REPLAN 结果"""
        await self.broadcast_to_task(task_id, {
            "type": "execution.replanned",
            "payload": {
                "from_step_id": from_step_id,
                "abandoned_steps": abandoned_steps,
                "new_steps": new_steps
            },
            "timestamp": self._timestamp(),
            "message_id": self._message_id()
        })
    
    async def push_execution_completed(self, task_id: str, blueprint, execution_time: float = 0):
        """推送执行完成"""
        steps = blueprint.steps if hasattr(blueprint, 'steps') else blueprint.get('steps', [])
        completed_count = sum(1 for s in steps 
                            if (s.status.value if hasattr(s, 'status') else s.get('status')) == "completed")
        
        await self.broadcast_to_task(task_id, {
            "type": "execution.completed",
            "payload": {
                "success": True,
                "summary": "任务执行完成",
                "completed_steps": completed_count,
                "total_steps": len(steps),
                "execution_time": execution_time,
                "can_save": True
            },
            "timestamp": self._timestamp(),
            "message_id": self._message_id()
        })
    
    async def push_execution_paused(self, task_id: str, blueprint_id: str):
        """推送执行暂停"""
        await self.broadcast_to_task(task_id, {
            "type": "execution.paused",
            "payload": {
                "blueprint_id": blueprint_id
            },
            "timestamp": self._timestamp(),
            "message_id": self._message_id()
        })
    
    async def push_execution_resumed(self, task_id: str, blueprint_id: str):
        """推送执行恢复"""
        await self.broadcast_to_task(task_id, {
            "type": "execution.resumed",
            "payload": {
                "blueprint_id": blueprint_id
            },
            "timestamp": self._timestamp(),
            "message_id": self._message_id()
        })
    
    # ========== Week 20 Vis-Adapter Methods ==========
    
    async def push_visual_preview(
        self,
        task_id: str,
        screenshot,
        analysis: dict
    ):
        """推送视觉预览"""
        elements = analysis.get("elements", [])
        elements_data = []
        for elem in elements:
            if hasattr(elem, 'to_dict'):
                elements_data.append(elem.to_dict())
            else:
                elements_data.append(elem)
        
        await self.broadcast_to_task(task_id, {
            "type": "vis.preview",
            "payload": {
                "screenshot_id": screenshot.id if hasattr(screenshot, 'id') else screenshot.get('id'),
                "image_base64": screenshot.base64 if hasattr(screenshot, 'base64') else screenshot.get('base64'),
                "width": screenshot.width if hasattr(screenshot, 'width') else screenshot.get('width'),
                "height": screenshot.height if hasattr(screenshot, 'height') else screenshot.get('height'),
                "annotations": screenshot.annotations if hasattr(screenshot, 'annotations') else screenshot.get('annotations', []),
                "analysis": {
                    "scene_type": analysis.get("scene_type"),
                    "elements": elements_data,
                    "suggested_next_action": analysis.get("suggested_next_action")
                }
            },
            "timestamp": self._timestamp(),
            "message_id": self._message_id()
        })
    
    async def push_visual_action_executed(self, task_id: str, action: str, result: dict):
        """推送视觉动作执行结果"""
        await self.broadcast_to_task(task_id, {
            "type": "vis.action_executed",
            "payload": {
                "action": action,
                "result": result
            },
            "timestamp": self._timestamp(),
            "message_id": self._message_id()
        })
    
    # ========== Utility Methods ==========
    
    def _timestamp(self) -> int:
        return int(datetime.now().timestamp() * 1000)
    
    def _message_id(self) -> str:
        import uuid
        return str(uuid.uuid4())
    
    def _calculate_duration(self, step) -> int:
        started = step.started_at if hasattr(step, 'started_at') else step.get('started_at')
        completed = step.completed_at if hasattr(step, 'completed_at') else step.get('completed_at')
        
        if started and completed:
            try:
                start = datetime.fromisoformat(started)
                end = datetime.fromisoformat(completed)
                return int((end - start).total_seconds() * 1000)
            except:
                pass
        return 0


# Global instance
state_sync = StateSyncManager()
