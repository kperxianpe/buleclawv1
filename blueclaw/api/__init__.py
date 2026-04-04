# -*- coding: utf-8 -*-
"""
blueclaw.api - API 模块

提供 WebSocket 通信、消息协议和引擎外观接口。

三层架构:
- message_protocol.py: 版本化消息协议定义
- engine_facade.py: 统一引擎外观（隐藏内部实现）
- websocket_server.py: WebSocket 服务器

使用示例:
    from blueclaw.api import create_server, create_engine_facade
    
    # 启动服务器
    server = create_server(host="localhost", port=8765)
    await server.start()
    
    # 或使用引擎外观直接编程
    engine = create_engine_facade()
    result = await engine.process("用户输入")
"""

from .message_protocol import (
    # 常量
    PROTOCOL_VERSION,
    
    # 枚举
    MessageType,
    NodeStatus,
    Phase,
    
    # 数据类
    ThinkingOptionData,
    ThinkingNodeData,
    ExecutionStepData,
    InterventionActionData,
    BlueclawMessage,
    
    # 工厂方法
    MessageFactory,
    
    # 工具函数
    check_version_compatibility,
    create_message,
)

from .engine_facade import (
    # 数据类
    ReplanResult,
    ThinkingResultData,
    EngineState,
    
    # 回调类型
    ThinkingNodeCreatedCallback,
    OptionSelectedCallback,
    BlueprintLoadedCallback,
    StepStatusChangedCallback,
    ExecutionCompletedCallback,
    InterventionNeededCallback,
    StateChangedCallback,
    MessageEmittedCallback,
    
    # 核心类
    BlueclawEngineFacade,
    create_engine_facade,
)

from .websocket_server import (
    ConnectionHandler,
    BlueclawWebSocketServer,
    create_server,
)

__all__ = [
    # 常量
    "PROTOCOL_VERSION",
    
    # 枚举
    "MessageType",
    "NodeStatus",
    "Phase",
    
    # 数据类
    "ThinkingOptionData",
    "ThinkingNodeData",
    "ExecutionStepData",
    "InterventionActionData",
    "BlueclawMessage",
    "ReplanResult",
    "ThinkingResultData",
    "EngineState",
    
    # 工厂方法
    "MessageFactory",
    
    # 工具函数
    "check_version_compatibility",
    "create_message",
    
    # 回调类型
    "ThinkingNodeCreatedCallback",
    "OptionSelectedCallback",
    "BlueprintLoadedCallback",
    "StepStatusChangedCallback",
    "ExecutionCompletedCallback",
    "InterventionNeededCallback",
    "StateChangedCallback",
    "MessageEmittedCallback",
    
    # 核心类
    "BlueclawEngineFacade",
    "create_engine_facade",
    "ConnectionHandler",
    "BlueclawWebSocketServer",
    "create_server",
]
