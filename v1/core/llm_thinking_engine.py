#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_thinking_engine.py - Blueclaw v1.0 LLM Thinking Engine

LLM 驱动的思考引擎 - 将思考引擎从基于规则升级为基于 LLM
支持智能意图识别、动态选项生成、多轮对话上下文管理
"""

import json
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import os

# 导入核心数据结构
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from core.thinking_engine import (
    IntentType, ThinkingStep, ThinkingOption, 
    ThinkingResult, ThinkingEngine as RuleBasedEngine
)


class LLMProvider(Enum):
    """LLM 提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOONSHOT = "moonshot"
    MOCK = "mock"  # 用于测试


@dataclass
class ConversationContext:
    """对话上下文"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    max_history: int = 10
    
    def add_message(self, role: str, content: str):
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # 保留最近消息
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]
    
    def get_recent_messages(self, n: int = 5) -> List[Dict[str, str]]:
        """获取最近 n 条消息"""
        recent = self.messages[-n:] if n < len(self.messages) else self.messages
        return [{"role": m["role"], "content": m["content"]} for m in recent]
    
    def to_llm_format(self, n: int = 5) -> List[Dict[str, str]]:
        """转换为 LLM 格式"""
        return self.get_recent_messages(n)
    
    def clear(self):
        """清空上下文"""
        self.messages.clear()


@dataclass
class LLMResponse:
    """LLM 响应"""
    intent: str
    confidence: float
    needs_blueprint: bool
    thinking_steps: List[Dict[str, Any]]
    direct_response: Optional[str] = None
    raw_response: str = ""
    latency_ms: float = 0.0


class LLMThinkingEngine:
    """
    LLM 驱动的思考引擎
    
    特点：
    - 基于 LLM 的意图识别（语义理解）
    - 动态选项生成
    - 多轮对话上下文管理
    - 支持多种 LLM 提供商
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model: str = "gpt-4",
                 provider: LLMProvider = LLMProvider.OPENAI,
                 use_mock: bool = False):
        """
        初始化 LLM 思考引擎
        
        Args:
            api_key: API 密钥
            model: 模型名称
            provider: LLM 提供商
            use_mock: 是否使用模拟模式（用于测试）
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.provider = provider if not use_mock else LLMProvider.MOCK
        
        # 初始化 LLM 客户端
        self.client = None
        self._init_client()
        
        # 上下文管理
        self.contexts: Dict[str, ConversationContext] = {}
        
        # 备用规则引擎（降级使用）
        self.fallback_engine = RuleBasedEngine()
        
        # 统计
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_latency_ms": 0.0
        }
        
    def _init_client(self):
        """初始化 LLM 客户端"""
        if self.provider == LLMProvider.OPENAI:
            try:
                import openai
                self.client = openai.AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                print("[LLMThinkingEngine] OpenAI package not installed, using mock mode")
                self.provider = LLMProvider.MOCK
                
        elif self.provider == LLMProvider.MOONSHOT:
            try:
                import openai
                # Moonshot 使用 OpenAI 兼容接口
                self.client = openai.AsyncOpenAI(
                    api_key=self.api_key,
                    base_url="https://api.moonshot.cn/v1"
                )
            except ImportError:
                print("[LLMThinkingEngine] OpenAI package not installed, using mock mode")
                self.provider = LLMProvider.MOCK
                
        elif self.provider == LLMProvider.ANTHROPIC:
            try:
                import anthropic
                self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
            except ImportError:
                print("[LLMThinkingEngine] Anthropic package not installed, using mock mode")
                self.provider = LLMProvider.MOCK
                
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个智能任务规划助手，名为 Blueclaw。你的任务是分析用户的任务描述，决定如何处理。

## 分析原则

1. **任务复杂度评估**：
   - 简单任务（如"查天气"、"讲个笑话"）-> 直接执行，不需要蓝图
   - 中等任务（如"写小红书"、"整理文件"）-> 确认关键细节，然后执行
   - 复杂任务（如"策划旅行"、"开发项目"）-> 多轮确认（目的地/时间/预算等）

2. **意图分类**：
   - create: 创建/生成内容
   - modify: 修改/更新内容
   - analyze: 分析/检查内容
   - execute: 执行命令/操作
   - question: 提问/咨询
   - chat: 闲聊/对话

3. **选项设计原则**：
   - 提供 2-4 个选项
   - 每个选项包含：label(A/B/C/D)、title、description、confidence(0-1)
   - 置信度基于匹配程度
   - 第一个选项默认是推荐选项

## 输出格式（JSON）

```json
{
    "intent": "create|modify|analyze|execute|question|chat",
    "confidence": 0.92,
    "needs_blueprint": true|false,
    "thinking_steps": [
        {
            "step_number": 1,
            "title": "步骤标题",
            "description": "详细描述",
            "status": "completed"
        }
    ],
    "options": [
        {
            "label": "A",
            "title": "选项标题",
            "description": "选项描述",
            "confidence": 0.95,
            "action": "action_name"
        }
    ],
    "direct_response": "如果不需要蓝图，直接回答的内容"
}
```

## 示例

用户："帮我写一个 Python 爬虫"
输出：
```json
{
    "intent": "create",
    "confidence": 0.95,
    "needs_blueprint": true,
    "thinking_steps": [
        {"step_number": 1, "title": "意图识别", "description": "用户需要创建 Python 爬虫", "status": "completed"},
        {"step_number": 2, "title": "需求分析", "description": "分析爬虫目标网站和数据需求", "status": "completed"}
    ],
    "options": [
        {"label": "A", "title": "快速生成", "description": "生成基础爬虫模板，适合简单页面", "confidence": 0.90, "action": "quick_template"},
        {"label": "B", "title": "确认需求", "description": "先确认目标网站和数据字段", "confidence": 0.85, "action": "clarify_requirements"},
        {"label": "C", "title": "高级定制", "description": "支持反爬、多线程等高级功能", "confidence": 0.75, "action": "advanced_crawler"}
    ]
}
```

用户："今天天气怎么样"
输出：
```json
{
    "intent": "question",
    "confidence": 0.98,
    "needs_blueprint": false,
    "thinking_steps": [
        {"step_number": 1, "title": "意图识别", "description": "用户询问天气", "status": "completed"}
    ],
    "options": [],
    "direct_response": "我来帮您查询今天的天气信息..."
}
```

请严格按照 JSON 格式输出，不要包含其他内容。"""

    async def analyze(self, user_input: str, 
                      context_id: str = "default",
                      timeout: float = 10.0) -> ThinkingResult:
        """
        分析用户输入
        
        Args:
            user_input: 用户输入
            context_id: 上下文 ID
            timeout: 超时时间（秒）
            
        Returns:
            ThinkingResult
        """
        start_time = datetime.now()
        self.stats["total_requests"] += 1
        
        # 获取或创建上下文
        if context_id not in self.contexts:
            self.contexts[context_id] = ConversationContext()
        context = self.contexts[context_id]
        
        try:
            # 调用 LLM
            if self.provider == LLMProvider.MOCK:
                llm_response = await self._mock_llm_call(user_input, context)
            else:
                llm_response = await self._call_llm(user_input, context, timeout)
            
            # 更新统计
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.stats["successful_requests"] += 1
            self._update_average_latency(latency)
            llm_response.latency_ms = latency
            
            # 解析响应
            result = self._parse_llm_response(llm_response)
            
            # 添加上下文
            context.add_message("user", user_input)
            context.add_message("assistant", f"Intent: {result.intent.value}")
            result.context["llm_latency_ms"] = latency
            result.context["context_id"] = context_id
            
            return result
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            print(f"[LLMThinkingEngine] LLM call failed: {e}, falling back to rule-based engine")
            
            # 降级到规则引擎
            result = self.fallback_engine.analyze(user_input)
            result.context["fallback_reason"] = str(e)
            result.context["llm_failed"] = True
            
            return result
    
    async def _call_llm(self, user_input: str, 
                        context: ConversationContext,
                        timeout: float) -> LLMResponse:
        """调用 LLM"""
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            *context.to_llm_format(5),
            {"role": "user", "content": user_input}
        ]
        
        if self.provider in [LLMProvider.OPENAI, LLMProvider.MOONSHOT]:
            return await self._call_openai_compatible(messages, timeout)
        elif self.provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(messages, timeout)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _call_openai_compatible(self, messages: List[Dict], 
                                       timeout: float) -> LLMResponse:
        """调用 OpenAI 兼容接口"""
        response = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1500,
                response_format={"type": "json_object"}
            ),
            timeout=timeout
        )
        
        content = response.choices[0].message.content
        return self._parse_llm_json_response(content)
    
    async def _call_anthropic(self, messages: List[Dict], 
                               timeout: float) -> LLMResponse:
        """调用 Anthropic Claude"""
        # 转换消息格式
        system_msg = ""
        user_msgs = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                user_msgs.append(msg)
        
        response = await asyncio.wait_for(
            self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.7,
                system=system_msg,
                messages=user_msgs
            ),
            timeout=timeout
        )
        
        content = response.content[0].text
        return self._parse_llm_json_response(content)
    
    async def _mock_llm_call(self, user_input: str, 
                             context: ConversationContext) -> LLMResponse:
        """模拟 LLM 调用（用于测试）"""
        await asyncio.sleep(0.5)  # 模拟延迟
        
        # 简单的规则匹配
        user_lower = user_input.lower()
        
        if any(word in user_lower for word in ["create", "make", "build", "写", "创建"]):
            return LLMResponse(
                intent="create",
                confidence=0.92,
                needs_blueprint=True,
                thinking_steps=[
                    {"step_number": 1, "title": "Intent Analysis", "description": "Identify user intent: create", "status": "completed"},
                    {"step_number": 2, "title": "Requirement Analysis", "description": "Extract creation requirements", "status": "completed"}
                ],
                options=[
                    {"label": "A", "title": "Quick Template", "description": "Use pre-built template for rapid creation", "confidence": 0.90, "action": "quick_template"},
                    {"label": "B", "title": "Custom Creation", "description": "Build from scratch with full customization", "confidence": 0.85, "action": "custom_create"},
                    {"label": "C", "title": "View Examples", "description": "See similar examples first", "confidence": 0.70, "action": "view_examples"}
                ],
                raw_response="mock_response"
            )
        elif any(word in user_lower for word in ["question", "what", "how", "为什么", "怎么"]):
            return LLMResponse(
                intent="question",
                confidence=0.95,
                needs_blueprint=False,
                thinking_steps=[
                    {"step_number": 1, "title": "Intent Analysis", "description": "Identify user intent: question", "status": "completed"}
                ],
                options=[
                    {"label": "A", "title": "Quick Answer", "description": "Give concise direct answer", "confidence": 0.95, "action": "quick_answer"},
                    {"label": "B", "title": "Detailed Explanation", "description": "Provide comprehensive explanation", "confidence": 0.80, "action": "detailed_explain"}
                ],
                direct_response="I'll help you with that question...",
                raw_response="mock_response"
            )
        else:
            return LLMResponse(
                intent="chat",
                confidence=0.80,
                needs_blueprint=False,
                thinking_steps=[
                    {"step_number": 1, "title": "Intent Analysis", "description": "Identify user intent: chat", "status": "completed"}
                ],
                options=[
                    {"label": "A", "title": "Continue Chat", "description": "Continue conversation", "confidence": 0.90, "action": "chat"},
                    {"label": "B", "title": "Start Task", "description": "Switch to task mode", "confidence": 0.70, "action": "start_task"}
                ],
                raw_response="mock_response"
            )
    
    def _parse_llm_json_response(self, content: str) -> LLMResponse:
        """解析 LLM JSON 响应"""
        try:
            # 提取 JSON（可能有 markdown 包裹）
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
                
            data = json.loads(content.strip())
            
            return LLMResponse(
                intent=data.get("intent", "unknown"),
                confidence=data.get("confidence", 0.5),
                needs_blueprint=data.get("needs_blueprint", True),
                thinking_steps=data.get("thinking_steps", []),
                options=data.get("options", []),
                direct_response=data.get("direct_response"),
                raw_response=content
            )
        except json.JSONDecodeError as e:
            print(f"[LLMThinkingEngine] Failed to parse JSON: {e}")
            # 返回默认值
            return LLMResponse(
                intent="unknown",
                confidence=0.5,
                needs_blueprint=True,
                thinking_steps=[],
                options=[],
                raw_response=content
            )
    
    def _parse_llm_response(self, llm_response: LLMResponse) -> ThinkingResult:
        """将 LLM 响应转换为 ThinkingResult"""
        # 转换意图
        try:
            intent = IntentType(llm_response.intent.lower())
        except ValueError:
            intent = IntentType.UNKNOWN
            
        # 转换思考步骤
        thinking_steps = []
        for i, step_data in enumerate(llm_response.thinking_steps):
            step = ThinkingStep(
                step_number=step_data.get("step_number", i + 1),
                icon="[*]" if i == 0 else "[~]" if i < len(llm_response.thinking_steps) - 1 else "[!]",
                title=step_data.get("title", f"Step {i+1}"),
                description=step_data.get("description", ""),
                status=step_data.get("status", "completed")
            )
            thinking_steps.append(step)
            
        # 转换选项
        options = []
        colors = ["#4caf50", "#2196f3", "#ff9800", "#9c27b0"]
        for i, opt_data in enumerate(llm_response.options[:4]):  # 最多4个选项
            option = ThinkingOption(
                option_id=opt_data.get("label", chr(65 + i)),
                label=opt_data.get("label", chr(65 + i)),
                icon=f"[{opt_data.get('label', chr(65 + i))}]",
                title=opt_data.get("title", f"Option {i+1}"),
                description=opt_data.get("description", ""),
                confidence=int(opt_data.get("confidence", 0.5) * 100),
                color=colors[i % len(colors)],
                action=opt_data.get("action", "default"),
                params={}
            )
            options.append(option)
            
        # 如果没有选项但不需要蓝图，创建默认选项
        if not options and not llm_response.needs_blueprint:
            options = [ThinkingOption(
                option_id="A",
                label="A",
                icon="[A]",
                title="Continue",
                description="Proceed with direct response",
                confidence=95,
                color="#4caf50",
                action="direct_response",
                params={"response": llm_response.direct_response or ""}
            )]
            
        return ThinkingResult(
            intent=intent,
            intent_confidence=llm_response.confidence,
            thinking_steps=thinking_steps,
            options=options,
            context={
                "needs_blueprint": llm_response.needs_blueprint,
                "direct_response": llm_response.direct_response,
                "llm_latency_ms": llm_response.latency_ms,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def _update_average_latency(self, new_latency: float):
        """更新平均延迟"""
        n = self.stats["successful_requests"]
        if n == 1:
            self.stats["average_latency_ms"] = new_latency
        else:
            old_avg = self.stats["average_latency_ms"]
            self.stats["average_latency_ms"] = (old_avg * (n - 1) + new_latency) / n
    
    def clear_context(self, context_id: str = "default"):
        """清空上下文"""
        if context_id in self.contexts:
            self.contexts[context_id].clear()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()
    
    def is_available(self) -> bool:
        """检查 LLM 是否可用"""
        if self.provider == LLMProvider.MOCK:
            return True
        return self.client is not None and bool(self.api_key)


# 便捷函数
def create_llm_thinking_engine(
    api_key: Optional[str] = None,
    model: str = "gpt-4",
    use_mock: bool = False
) -> LLMThinkingEngine:
    """
    创建 LLM 思考引擎
    
    Args:
        api_key: API 密钥（默认从环境变量读取）
        model: 模型名称
        use_mock: 是否使用模拟模式
        
    Returns:
        LLMThinkingEngine 实例
    """
    return LLMThinkingEngine(
        api_key=api_key,
        model=model,
        use_mock=use_mock
    )
