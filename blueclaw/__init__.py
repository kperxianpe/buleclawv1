# -*- coding: utf-8 -*-
"""
Blueclaw v1.0 - AI Self-Operating Canvas Framework

A modular blueprint engine with AI self-operation capabilities.

Quick Start:
    >>> from blueclaw import create_coordinator_v3
    >>> coord = create_coordinator_v3(use_real_execution=True)
    >>> await coord.start_task("List files in directory")
"""

__version__ = "1.0.0"

# Core components
from .core.dynamic_thinking_engine import (
    DynamicThinkingEngine, ThinkingResult, ThinkingResultType,
    ThinkingOption, ClarificationQuestion, create_dynamic_thinking_engine
)
from .core.execution_blueprint import (
    ExecutionBlueprintSystem, ExecutionStep, StepStatus,
    create_execution_blueprint_system
)

# Skills (OpenClaw integration)
from .skills import (
    BaseSkill, SkillResult, SkillParameter, PermissionLevel,
    SkillRegistry, get_registry,
    FileSkill, ShellSkill, CodeSkill, SearchSkill, BrowserSkill
)

# Memory (OpenClaw integration)
from .memory import (
    MemoryManager, WorkingMemory, LongTermMemory
)

# Integration
from .integration.coordinator_v3 import (
    ApplicationCoordinatorV3, ApplicationState, create_coordinator_v3
)

__all__ = [
    # Version
    "__version__",
    # Core
    "DynamicThinkingEngine", "ThinkingResult", "ThinkingResultType",
    "ThinkingOption", "ClarificationQuestion", "create_dynamic_thinking_engine",
    "ExecutionBlueprintSystem", "ExecutionStep", "StepStatus",
    "create_execution_blueprint_system",
    # Skills
    "BaseSkill", "SkillResult", "SkillParameter", "PermissionLevel",
    "SkillRegistry", "get_registry",
    "FileSkill", "ShellSkill", "CodeSkill", "SearchSkill", "BrowserSkill",
    # Memory
    "MemoryManager", "WorkingMemory", "LongTermMemory",
    # Integration
    "ApplicationCoordinatorV3", "ApplicationState", "create_coordinator_v3",
]
