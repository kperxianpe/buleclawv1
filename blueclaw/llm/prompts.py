#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt 模板库
"""

THINKING_OPTIONS_PROMPT = """你是一个智能助手。用户当前需求: {context}

请生成3-4个选项供用户选择，帮助逐步明确需求。

要求:
1. 每个选项有标签(简短)和描述(详细)
2. 给出置信度(0-1)，标记最推荐的选项
3. 选项应该涵盖不同的处理方式

输出格式(JSON):
{{
  "question": "向用户展示的问题",
  "options": [
    {{
      "id": "A",
      "label": "选项标签",
      "description": "详细描述",
      "confidence": 0.95,
      "recommended": true
    }}
  ]
}}"""

EXECUTION_STEPS_PROMPT = """基于用户决策路径，生成执行步骤。

决策路径:
{thinking_path}

每个步骤包含:
1. name: 步骤名称
2. direction: AI在做什么
3. example: 预期结果示例
4. validation: 如何判断成功
5. tool: 使用什么工具（Skill名称）
6. dependencies: 依赖的步骤ID列表

输出格式(JSON):
{{
  "steps": [
    {{
      "name": "步骤名称",
      "direction": "AI执行的方向",
      "example": "预期结果示例",
      "validation": "验证规则",
      "tool": "SkillName",
      "dependencies": []
    }}
  ]
}}"""


def format_thinking_options_prompt(context: str, history: list) -> str:
    """格式化思考选项提示词"""
    return THINKING_OPTIONS_PROMPT.format(context=context)


def format_execution_steps_prompt(thinking_path: list) -> str:
    """格式化执行步骤提示词"""
    import json
    return EXECUTION_STEPS_PROMPT.format(
        thinking_path=json.dumps(thinking_path, ensure_ascii=False, indent=2)
    )
