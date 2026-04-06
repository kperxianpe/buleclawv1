#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Message Router - Complete implementation with all 8 handlers

Handlers:
1. task.start
2. thinking.select_option
3. thinking.custom_input  
4. thinking.confirm_execution
5. execution.start
6. execution.pause
7. execution.resume
8. execution.intervene
"""

import json
from typing import Dict, Optional
from datetime import datetime

from backend.core.task_manager import task_manager
from backend.core.checkpoint import checkpoint_manager
from blueclaw.api.engine_facade import BlueclawEngineFacade
from blueclaw.core.thinking_engine import thinking_engine
from blueclaw.core.execution_engine import execution_engine
from blueclaw.core.state_sync import state_sync
from blueclaw.api.messages import Message

# Week 20 Vis-Adapter imports
from backend.vis import vms, vlm, mpl, hee
from backend.vis.hybrid_executor import ExecutionMode


class MessageRouter:
    """消息路由器"""
    
    def __init__(self):
        self.handlers = {
            # Task handlers
            "task.start": self._handle_task_start,
            "task.interrupt": self._handle_task_interrupt,
            
            # Thinking handlers
            "thinking.select_option": self._handle_thinking_select_option,
            "thinking.custom_input": self._handle_thinking_custom_input,
            "thinking.confirm_execution": self._handle_thinking_confirm_execution,
            
            # Execution handlers
            "execution.start": self._handle_execution_start,
            "execution.pause": self._handle_execution_pause,
            "execution.resume": self._handle_execution_resume,
            "execution.intervene": self._handle_execution_intervene,
            
            # Week 20 Vis-Adapter handlers
            "vis.preview": self._handle_vis_preview,
            "vis.user_selection": self._handle_vis_user_selection,
            "vis.confirm": self._handle_vis_confirm,
            "vis.skip": self._handle_vis_skip,
            "vis.batch_confirm": self._handle_vis_batch_confirm,
            "vis.action": self._handle_vis_action,
        }
        self.facades: Dict[str, BlueclawEngineFacade] = {}
    
    def set_websocket_server(self, server):
        state_sync.set_websocket_server(server)
    
    async def route(self, websocket, message: dict, server) -> dict:
        """路由消息到对应处理器"""
        msg_type = message.get("type", "unknown")
        payload = message.get("payload", {})
        
        handler = self.handlers.get(msg_type)
        if handler:
            return await handler(websocket, payload, server)
        
        return {"type": "error", "error": f"Unknown message type: {msg_type}"}
    
    # ========== Task Handlers ==========
    
    async def _handle_task_start(self, websocket, payload: dict, server) -> dict:
        """Handler 1: 任务启动"""
        user_input = payload.get("user_input", "")
        
        # 1. 创建任务
        task = await task_manager.create_task(user_input)
        
        # 2. 关联连接与任务
        server.associate_connection_with_task(websocket, task.id)
        
        # 3. 创建 EngineFacade
        facade = BlueclawEngineFacade(task.id)
        self.facades[task.id] = facade
        
        # 4. 调用思考引擎开始思考
        root_node = await thinking_engine.start_thinking(task.id, user_input)
        
        # 5. 推送思考节点
        await state_sync.push_thinking_node_created(task.id, root_node, is_root=True)
        
        return Message.task_started(task.id, user_input)
    
    async def _handle_task_interrupt(self, websocket, payload: dict, server) -> dict:
        """处理任务中断"""
        task_id = payload.get("task_id", "")
        # 实现任务中断逻辑
        return {"type": "task.interrupted", "payload": {"task_id": task_id}}
    
    # ========== Thinking Handlers ==========
    
    async def _handle_thinking_select_option(self, websocket, payload: dict, server) -> dict:
        """Handler 2: 选择思考选项"""
        task_id = payload.get("task_id", "")
        option_id = payload.get("option_id", "")
        current_node_id = payload.get("current_node_id", "")
        
        if not task_id or not option_id:
            return {"type": "error", "error": "Missing task_id or option_id"}
        
        # 1. 选择选项并获取下一层
        result = await thinking_engine.select_option(
            task_id=task_id,
            node_id=current_node_id,
            option_id=option_id
        )
        
        # 2. 保存checkpoint
        await checkpoint_manager.save_checkpoint(task_manager.get_task(task_id))
        
        # 3. 推送节点更新
        if result.get("has_more_options"):
            # 还有下一层，推送新选项
            next_node = result.get("next_node")
            await state_sync.push_thinking_node_created(task_id, next_node, is_root=False)
            return Message.thinking_option_selected(task_id, option_id, has_more=True)
        else:
            # 收敛完成，推送最终路径
            final_path = result.get("final_path", [])
            await state_sync.push_thinking_completed(task_id, final_path)
            return Message.thinking_option_selected(task_id, option_id, has_more=False, final_path=final_path)
    
    async def _handle_thinking_custom_input(self, websocket, payload: dict, server) -> dict:
        """Handler 3: 自定义输入（第4个白块）"""
        task_id = payload.get("task_id", "")
        custom_input = payload.get("custom_input", "")
        current_node_id = payload.get("current_node_id", "")
        
        if not task_id or not custom_input:
            return {"type": "error", "error": "Missing task_id or custom_input"}
        
        # 1. 使用自定义输入继续思考
        result = await thinking_engine.select_custom_input(
            task_id=task_id,
            node_id=current_node_id,
            custom_input=custom_input
        )
        
        # 2. 保存checkpoint
        await checkpoint_manager.save_checkpoint(task_manager.get_task(task_id))
        
        # 3. 推送节点更新
        if result.get("has_more_options"):
            next_node = result.get("next_node")
            await state_sync.push_thinking_node_created(task_id, next_node, is_root=False)
            return Message.thinking_custom_input_received(task_id, has_more=True)
        else:
            final_path = result.get("final_path", [])
            await state_sync.push_thinking_completed(task_id, final_path)
            return Message.thinking_custom_input_received(task_id, has_more=False, final_path=final_path)
    
    async def _handle_thinking_confirm_execution(self, websocket, payload: dict, server) -> dict:
        """Handler 4: 确认执行"""
        task_id = payload.get("task_id", "")
        
        # 1. 获取最终思考路径
        final_path = thinking_engine.get_final_path(task_id)
        
        # 2. 更新任务状态
        await task_manager.update_task_status(task_id, "EXECUTING")
        
        # 3. 生成执行蓝图
        blueprint = await execution_engine.create_blueprint(task_id, final_path)
        
        # 4. 推送蓝图加载
        await state_sync.push_execution_blueprint_loaded(task_id, blueprint)
        
        return Message.thinking_execution_confirmed(task_id, blueprint.id, blueprint.to_dict() if hasattr(blueprint, 'to_dict') else {})
    
    # ========== Execution Handlers ==========
    
    async def _handle_execution_start(self, websocket, payload: dict, server) -> dict:
        """Handler 5: 开始执行"""
        task_id = payload.get("task_id", "")
        blueprint_id = payload.get("blueprint_id", "")
        
        if not task_id or not blueprint_id:
            return {"type": "error", "error": "Missing task_id or blueprint_id"}
        
        # 启动执行
        success = await execution_engine.start_execution(blueprint_id)
        
        if success:
            return Message.execution_started(task_id, blueprint_id)
        else:
            return {"type": "error", "error": "Failed to start execution"}
    
    async def _handle_execution_pause(self, websocket, payload: dict, server) -> dict:
        """Handler 6: 暂停执行"""
        task_id = payload.get("task_id", "")
        blueprint_id = payload.get("blueprint_id", "")
        
        if blueprint_id:
            await execution_engine.pause_execution(blueprint_id)
            await state_sync.push_execution_paused(task_id, blueprint_id)
            return Message.execution_paused(task_id, blueprint_id)
        
        return {"type": "error", "error": "Missing blueprint_id"}
    
    async def _handle_execution_resume(self, websocket, payload: dict, server) -> dict:
        """Handler 7: 恢复执行"""
        task_id = payload.get("task_id", "")
        blueprint_id = payload.get("blueprint_id", "")
        
        if blueprint_id:
            success = await execution_engine.resume_execution(blueprint_id)
            if success:
                await state_sync.push_execution_resumed(task_id, blueprint_id)
                return Message.execution_resumed(task_id, blueprint_id)
            else:
                return {"type": "error", "error": "Execution not in paused state"}
        
        return {"type": "error", "error": "Missing blueprint_id"}
    
    async def _handle_execution_intervene(self, websocket, payload: dict, server) -> dict:
        """Handler 8: 用户干预"""
        task_id = payload.get("task_id", "")
        blueprint_id = payload.get("blueprint_id", "")
        step_id = payload.get("step_id", "")
        action = payload.get("action", "")  # replan, skip, retry, modify
        custom_input = payload.get("custom_input", "")
        
        if not all([blueprint_id, step_id, action]):
            return {"type": "error", "error": "Missing required parameters"}
        
        # 构建干预数据
        intervention_data = {}
        if custom_input:
            intervention_data["custom_input"] = custom_input
        if "direction" in payload:
            intervention_data["direction"] = payload["direction"]
        
        # 执行干预
        result = await execution_engine.handle_intervention(
            blueprint_id=blueprint_id,
            step_id=step_id,
            action=action,
            data=intervention_data
        )
        
        if result and result.get("action") == "replan":
            # REPLAN: 推送更新
            new_steps = result.get("new_steps", [])
            await state_sync.push_execution_replanned(
                task_id, step_id,
                abandoned_steps=[],
                new_steps=new_steps
            )
            return Message.execution_intervened(task_id, blueprint_id, step_id, action, {
                "new_steps": new_steps
            })
        
        return Message.execution_intervened(task_id, blueprint_id, step_id, action, result or {})
    
    # ========== Week 20 Vis-Adapter Handlers ==========
    
    async def _handle_vis_preview(self, websocket, payload: dict, server) -> dict:
        """
        vis.preview -> 请求视觉预览
        后端截图并通过 WebSocket 推送
        """
        task_id = payload.get("task_id", "")
        region = payload.get("region")  # 可选: {"x", "y", "width", "height"}
        task_description = payload.get("task_description", "")
        
        if not task_id:
            return {"type": "error", "error": "Missing task_id"}
        
        # 截图
        if region:
            screenshot = await vms.capture_region(
                task_id, int(region["x"]), int(region["y"]), 
                int(region["width"]), int(region["height"])
            )
        else:
            screenshot = await vms.capture_fullscreen(task_id)
        
        if screenshot:
            # 分析截图
            analysis = await vlm.analyze_screenshot(
                screenshot.base64,
                task_description
            )
            
            # 推送视觉反馈
            await state_sync.push_visual_preview(task_id, screenshot, analysis)
            
            return {
                "type": "vis.preview_ready",
                "payload": {
                    "screenshot_id": screenshot.id,
                    "width": screenshot.width,
                    "height": screenshot.height,
                    "elements_count": len(analysis.get("elements", [])),
                    "analysis": {
                        "scene_type": analysis.get("scene_type"),
                        "suggested_next_action": analysis.get("suggested_next_action")
                    }
                }
            }
        
        return {"type": "error", "error": "Screenshot failed"}
    
    async def _handle_vis_user_selection(self, websocket, payload: dict, server) -> dict:
        """
        vis.user_selection -> 用户圈选反馈
        前端用户圈选了某个区域，后端接收坐标并分析
        """
        task_id = payload.get("task_id", "")
        screenshot_id = payload.get("screenshot_id", "")
        selection = payload.get("selection", {})  # {"x", "y", "width", "height"}
        
        screenshot = vms.get_screenshot(screenshot_id)
        if not screenshot:
            return {"type": "error", "error": "Screenshot not found"}
        
        # 在截图上添加用户圈选标注
        vms.add_annotation(
            screenshot_id,
            "rect",
            selection,
            label="用户圈选",
            color="#FF6B35"
        )
        
        # 对圈选区域进行详细分析
        region_screenshot = await vms.capture_region(
            task_id,
            int(selection.get("x", 0)),
            int(selection.get("y", 0)),
            int(selection.get("width", 100)),
            int(selection.get("height", 100))
        )
        
        if region_screenshot:
            analysis = await vlm.analyze_screenshot(
                region_screenshot.base64,
                "分析用户圈选的区域"
            )
            
            return {
                "type": "vis.selection_analyzed",
                "payload": {
                    "selection": selection,
                    "analysis": analysis,
                    "region_screenshot_id": region_screenshot.id
                }
            }
        
        return {"type": "error", "error": "Region analysis failed"}
    
    async def _handle_vis_confirm(self, websocket, payload: dict, server) -> dict:
        """
        vis.confirm -> 确认视觉识别结果并执行
        """
        task_id = payload.get("task_id", "")
        screenshot_id = payload.get("screenshot_id", "")
        action = payload.get("action", "click")  # click, double_click, drag, etc.
        
        result = None
        
        if action == "click":
            x = payload.get("x", 0)
            y = payload.get("y", 0)
            result = await mpl.click(x, y)
        elif action == "double_click":
            x = payload.get("x", 0)
            y = payload.get("y", 0)
            result = await mpl.double_click(x, y)
        elif action == "right_click":
            x = payload.get("x", 0)
            y = payload.get("y", 0)
            result = await mpl.right_click(x, y)
        elif action == "drag":
            result = await mpl.drag(
                payload.get("start_x", 0),
                payload.get("start_y", 0),
                payload.get("end_x", 0),
                payload.get("end_y", 0)
            )
        elif action == "type":
            result = await mpl.type_text(payload.get("text", ""))
        elif action == "keypress":
            result = await mpl.keypress(payload.get("keys", []))
        
        return {
            "type": "vis.action_executed",
            "payload": {
                "action": action,
                "result": result.to_dict() if result else None
            }
        }
    
    async def _handle_vis_skip(self, websocket, payload: dict, server) -> dict:
        """
        vis.skip -> 跳过当前视觉步骤
        """
        task_id = payload.get("task_id", "")
        
        return {
            "type": "vis.skipped",
            "payload": {"message": "Visual step skipped", "task_id": task_id}
        }
    
    async def _handle_vis_batch_confirm(self, websocket, payload: dict, server) -> dict:
        """
        vis.batch_confirm -> 批量确认多个操作
        """
        task_id = payload.get("task_id", "")
        actions = payload.get("actions", [])  # [{"action": "click", "x": ..., "y": ...}, ...]
        
        results = await hee.execute_action_sequence(task_id, actions)
        
        return {
            "type": "vis.batch_executed",
            "payload": results
        }
    
    async def _handle_vis_action(self, websocket, payload: dict, server) -> dict:
        """
        vis.action -> 执行单个视觉动作（简化接口）
        """
        task_id = payload.get("task_id", "")
        action_def = payload.get("action_def", {})
        
        result = await mpl.execute_action(action_def)
        
        return {
            "type": "vis.action_result",
            "payload": {
                "action": action_def.get("action"),
                "result": result.to_dict()
            }
        }


# Global router instance
router = MessageRouter()
