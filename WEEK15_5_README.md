# Week 15.5 - Blueclaw 三层架构实现文档

## 概述

本文档描述 Blueclaw v1.0 的 Week 15.5 三层架构实现，支持向前兼容：
- **V1**: ReactFlow 渲染 (当前)
- **V2**: CanvasMind 画布引擎 (未来)
- **V3**: Adapter 系统 (未来)

## 快速开始

### 环境需求

```bash
# Python 3.10+
pip install websockets

# 可选：前端开发需要 Node.js 18+
# cd blueclaw-ui && npm install
```

### 1分钟快速测试

```bash
# 运行完整架构测试（自动启动服务器、测试、关闭）
python simple_1minute_test.py
```

预期输出：
```
============================================================
Week 15.5 - 1 Minute Architecture Test
============================================================
...
Tests passed: 20
Tests failed: 0

ALL TESTS PASSED!

Architecture:
  [OK] Protocol Layer (v1.0.0)
  [OK] Engine Facade Layer
  [OK] Renderer Adapter Layer
  [OK] WebSocket Communication
```

---

## 三层架构详解

```
+-----------------------------------------+
|  表现层 (Presentation)                   |
|  V1: ReactFlow 节点渲染                  |
|  V2: CanvasMind 画布引擎                 |
|  原则: 可替换，业务逻辑不依赖具体渲染实现  |
+-----------------------------------------+
|  协议层 (Protocol)                       |
|  稳定: WebSocket 消息格式 (v1.0.0)        |
|  稳定: Blueprint 数据结构                 |
|  原则: V1/V2/V3 消息格式保持一致          |
+-----------------------------------------+
|  引擎层 (Engine)                         |
|  V1: DynamicThinkingEngine               |
|  V2: + CanvasMind 内核                   |
|  V3: + Adapter 系统 + HEE                |
|  原则: 接口稳定，内部实现可演进            |
+-----------------------------------------+
```

---

## 后端接口层使用文档

### 1. 消息协议层

**文件**: `blueclaw/api/message_protocol.py`

**用途**: 定义版本化的消息格式，确保前后端兼容

**核心类**:
```python
from blueclaw.api import (
    PROTOCOL_VERSION,      # "1.0.0"
    MessageType,           # 消息类型枚举
    MessageFactory,        # 消息工厂
    BlueclawMessage,       # 基础消息类
    ThinkingNodeData,      # 思考节点数据
    ExecutionStepData,     # 执行步骤数据
)
```

**使用示例**:
```python
from blueclaw.api import MessageFactory, MessageType

# 创建任务开始消息
msg = MessageFactory.create_task_start("规划一个周末旅行")

# 序列化为 JSON
json_str = msg.to_json()

# 从 JSON 反序列化
parsed = BlueclawMessage.from_json(json_str)
```

### 2. 引擎外观层

**文件**: `blueclaw/api/engine_facade.py`

**用途**: 统一引擎入口，隐藏内部实现细节

**核心接口**:
```python
from blueclaw.api import create_engine_facade

# 创建引擎实例
engine = create_engine_facade(session_id="session-001")

# 处理用户输入
result = await engine.process("用户输入")

# 选择选项
result = await engine.select_option(node_id, option_id)

# 干预执行
result = await engine.intervene(step_id, action_type, custom_input)

# 设置回调
engine.set_callbacks(
    on_thinking_node_created=callback_func,
    on_blueprint_loaded=callback_func,
    state_changed=callback_func,
)
```

### 3. WebSocket 服务器

**文件**: `blueclaw/api/websocket_server.py`

**启动服务器**:
```bash
python start_websocket_server.py
# 或指定参数
python start_websocket_server.py --host 0.0.0.0 --port 8765
```

---

## 前端接口层使用文档

### 1. 消息协议

**文件**: `blueclaw-ui/src/core/protocol/messageTypes.ts`

**核心导出**:
```typescript
import {
  PROTOCOL_VERSION,
  MessageType,
  MessageFactory,
  BlueclawMessage,
  ThinkingNodeData,
  ExecutionStepData,
  NodeStatus,
  Phase,
} from './core/protocol/messageTypes';
```

### 2. 引擎客户端

**文件**: `blueclaw-ui/src/core/engine/BlueclawEngine.ts`

```typescript
import { BlueclawEngine, createEngine } from './core/engine/BlueclawEngine';

// 创建引擎客户端
const engine = createEngine('ws://localhost:8765', {
  onConnect: (sessionId) => console.log('Connected:', sessionId),
  onThinkingNodeCreated: (node) => console.log('Node:', node),
  onBlueprintLoaded: (steps) => console.log('Steps:', steps),
});

// 连接服务器
await engine.connect();

// 发送任务
engine.startTask("规划一个周末旅行");
```

### 3. 状态管理

**文件**: `blueclaw-ui/src/core/state/BlueprintStore.ts`

```typescript
import { 
  useConnectionState, 
  usePhaseState,
  useThinkingNodes,
  useExecutionSteps 
} from './core/state/BlueprintStore';

// 获取连接状态
const { isConnected, sessionId } = useConnectionState();

// 获取阶段状态
const { phase, progress, statusMessage } = usePhaseState();

// 获取思考节点
const { nodes, activeNodeId } = useThinkingNodes();

// 获取执行步骤
const { steps, currentStepId } = useExecutionSteps();
```

### 4. 渲染适配器

**文件**: `blueclaw-ui/src/adapters/BlueprintRenderer.ts`

**切换渲染器**:
```typescript
import { createRenderer } from './adapters/BlueprintRenderer';

// V1: ReactFlow
const renderer = createRenderer({ 
  type: 'reactflow', 
  container: document.getElementById('canvas') 
});

// V2: CanvasMind（未来）
const renderer = createRenderer({ 
  type: 'canvasmind', 
  container: document.getElementById('canvas') 
});
```

---

## 前后端连接指南

### 完整数据流

```
用户输入
    |
[前端] App.tsx
    - 收集用户输入
    - 调用 engine.startTask()
    |
[前端] BlueclawEngine.ts
    - 创建 MessageFactory.createTaskStart()
    - 通过 WebSocket 发送到后端
    |
[后端] WebSocketServer
    - 路由到 ConnectionHandler
    - 调用 BlueclawEngineFacade
    |
[后端] BlueclawEngineFacade
    - 调用 DynamicThinkingEngine
    - 生成思考节点/执行蓝图
    - 触发回调发送消息到前端
    |
[前端] BlueclawEngine.ts
    - 接收消息，调用对应回调
    - 更新 BlueprintStore
    |
[前端] BlueprintStore (Zustand)
    - 更新状态
    - 触发 React 组件重渲染
    |
[前端] ReactFlowAdapter
    - 监听状态变化
    - 更新 ReactFlow 节点/边
    |
用户看到更新后的画布
```

### 连接配置

**后端配置**:
```python
HOST = "localhost"  # 或 "0.0.0.0" 允许外部访问
PORT = 8765         # WebSocket 端口
```

**前端配置**:
```typescript
const WS_URL = 'ws://localhost:8765';
```

### 开发环境连接

```bash
# 终端 1: 启动后端
python start_websocket_server.py

# 终端 2: 启动前端开发服务器（如果有 Node.js）
cd blueclaw-ui
npm install
npm run dev

# 或终端 2: 使用 Python 测试客户端
python test_websocket_client.py
```

---

## 测试文档

### 测试文件清单

| 文件 | 用途 | 运行方式 |
|------|------|----------|
| `simple_1minute_test.py` | 1分钟完整架构测试 | `python simple_1minute_test.py` |
| `week15_5_verification.py` | 架构验证测试 | `python week15_5_verification.py` |
| `demo_architecture.py` | 架构演示 | `python demo_architecture.py` |
| `test_websocket_client.py` | 交互式 WebSocket 测试 | `python test_websocket_client.py` |

### simple_1minute_test.py（推荐）

**功能**: 自动测试所有三层架构

**运行**:
```bash
python simple_1minute_test.py
```

**预期效果**:
```
============================================================
Week 15.5 - 1 Minute Architecture Test
============================================================

[21:24:27] TEST 1: Protocol Layer
[21:24:27]   [PASS] Protocol version: 1.0.0
[21:24:27]   [PASS] Task message created with version
[21:24:27]   [PASS] Client->Server: 16 types
[21:24:27]   [PASS] Server->Client: 12 types
[21:24:27]   [PASS] Version 1.0.0 is compatible

[21:24:27] TEST 2: Engine Facade Layer
[21:24:27]   [PASS] Facade created: test-session
[21:24:27]   [PASS] All 7 interface methods present
[21:24:27]   [PASS] Initial state: Phase.IDLE
[21:24:27]   [PASS] Callbacks set

[21:24:27] TEST 3: Renderer Adapter Layer
[21:24:27]   [PASS] BlueprintRenderer.ts
[21:24:27]   [PASS] ReactFlowAdapter.ts
[21:24:27]   [PASS] CanvasMindAdapter.ts
[21:24:27]   [PASS] All 6 interface methods defined
[21:24:27]   [PASS] Renderer factory registration

[21:24:27] TEST 4: WebSocket Server (in-memory)
[21:24:27]   [PASS] Client connected
[21:24:27]   [PASS] Received: MessageType.CONNECTED
[21:24:27]   [PASS] Sent: MessageType.TASK_START
[21:24:27]   [PASS] Received: MessageType.THINKING_NODE_CREATED
[21:24:27]   [PASS] Server stopped

[21:25:27] ============================================================
[21:25:27] TEST SUMMARY
[21:25:27] ============================================================
[21:25:27] Total time: 60.0 seconds
[21:25:27] Tests passed: 20
[21:25:27] Tests failed: 0
[21:25:27] 
[21:25:27] ALL TESTS PASSED!
```

**测试内容**:
- 协议层: 版本检查、消息创建、序列化、兼容性
- 引擎外观层: Facade 创建、接口方法、状态管理、回调
- 渲染适配器层: 文件存在性、接口定义、工厂注册
- WebSocket 服务器: 启动、连接、消息收发

### week15_5_verification.py

**功能**: 验证架构实现是否符合 Week 15.5 要求

**运行**:
```bash
python week15_5_verification.py
```

### test_websocket_client.py

**功能**: 交互式 WebSocket 客户端测试

**运行**:
```bash
# 先启动服务器
python start_websocket_server.py

# 再启动客户端（另一个终端）
python test_websocket_client.py
```

**交互命令**:
```
> task 规划一个周末旅行     # 发送任务
> select thinking_001 A     # 选择选项
> intervene step_1 replan   # 干预执行
> quit                      # 退出
```

---

## 开发原则

写代码时问自己这三个问题：

| 问题 | 检查点 |
|------|--------|
| **这个消息格式 V2 还能用吗？** | 必须使用 `MessageFactory` 创建消息，包含 `version` 字段 |
| **这个接口 CanvasMind 能接入吗？** | 必须通过 `BlueprintRenderer` 接口操作渲染，不能直接调用 ReactFlow API |
| **这个数据结构 Adapter 系统能理解吗？** | 必须使用纯数据对象，不含渲染信息 |

---

## 文件结构

```
blueclaw/
├── api/                           # API 模块
│   ├── __init__.py               # 模块导出
│   ├── message_protocol.py       # 消息协议（版本化）
│   ├── engine_facade.py          # 引擎外观
│   └── websocket_server.py       # WebSocket 服务
├── core/                          # 核心引擎
│   ├── dynamic_thinking_engine.py
│   └── execution_blueprint.py
└── ...

blueclaw-ui/                       # 前端
├── src/
│   ├── core/                      # 核心层（不依赖渲染）
│   │   ├── protocol/
│   │   │   └── messageTypes.ts   # 消息协议定义
│   │   ├── engine/
│   │   │   └── BlueclawEngine.ts # 引擎客户端
│   │   └── state/
│   │       └── BlueprintStore.ts # 状态管理
│   ├── adapters/                  # 渲染适配器
│   │   ├── BlueprintRenderer.ts  # 渲染器接口
│   │   ├── reactflow/            # V1: ReactFlow 实现
│   │   └── canvasmind/           # V2: CanvasMind 实现（占位）
│   └── app/
│       └── App.tsx               # 主应用
├── package.json
└── vite.config.ts

# 测试和启动脚本
start_websocket_server.py          # 启动 WebSocket 服务器
test_websocket_client.py           # 交互式测试客户端
simple_1minute_test.py             # 1分钟自动测试
week15_5_verification.py           # 架构验证测试
demo_architecture.py               # 架构演示
WEEK15_5_README.md                 # 本文档
```

---

## 下一步开发

### 后端开发

可以开始实现：
1. **真实的思考引擎**: 接入 LLM API（OpenAI、Claude 等）
2. **Skill 执行系统**: 实现文件操作、代码执行等真实功能
3. **干预逻辑**: 完善 replan、skip、stop 等操作的实际逻辑

### 前端开发

可以开始实现：
1. **用户界面**: 输入框、选项按钮、干预面板
2. **动画效果**: 节点脉冲、路径高亮、过渡动画
3. **响应式设计**: 适配不同屏幕尺寸

### V2 迁移准备

CanvasMind 迁移步骤：
1. 实现 `CanvasMindAdapter` 类（替换占位实现）
2. 修改 `App.tsx` 中的 `rendererType` 为 `'canvasmind'`
3. 业务代码无需修改（接口保持一致）

---

## 常见问题

### Q: 浏览器访问 WebSocket 服务器报错？
**A**: 这是预期行为。WebSocket 服务器只能接受 WebSocket 连接，不能处理 HTTP 请求。请使用 `python test_websocket_client.py` 或 `python simple_1minute_test.py` 进行测试。

### Q: 如何验证架构实现正确？
**A**: 运行 `python simple_1minute_test.py`，如果显示 `ALL TESTS PASSED!` 则说明架构实现正确。

### Q: 如何切换渲染引擎（ReactFlow -> CanvasMind）？
**A**: 修改 `App.tsx` 中的 `const [rendererType, setRendererType] = useState<RendererType>('reactflow')` 为 `'canvasmind'`。业务代码无需修改。

### Q: 消息协议版本如何升级？
**A**: 修改 `PROTOCOL_VERSION` 常量（当前为 `"1.0.0"`），并确保 `check_version_compatibility()` 函数能处理新版本兼容性。

---

## 总结

- ✅ **协议层**: 稳定，版本化消息格式 v1.0.0
- ✅ **引擎外观层**: 稳定，接口定义完成，内部可替换
- ✅ **渲染适配器层**: 就绪，ReactFlow 实现完成，CanvasMind 占位
- ✅ **WebSocket 通信**: 正常，测试通过

**可以开始前后端并行开发！**
