# Week 15.5 架构实现文档

## 概述

本文档描述 Blueclaw v1.0 的 Week 15.5 三层架构实现，支持向前兼容：
- **V1**: ReactFlow 渲染 (当前)
- **V2**: CanvasMind 画布引擎 (未来)
- **V3**: Adapter 系统 (未来)

## 三层架构

```
┌─────────────────────────────────────────┐
│  表现层 (Presentation)                   │
│  V1: ReactFlow 节点渲染                  │
│  V2: CanvasMind 画布引擎                 │
│  原则: 可替换，业务逻辑不依赖具体渲染实现  │
├─────────────────────────────────────────┤
│  协议层 (Protocol)                       │
│  稳定: WebSocket 消息格式 (v1.0.0)        │
│  稳定: Blueprint 数据结构                 │
│  原则: V1/V2/V3 消息格式保持一致          │
├─────────────────────────────────────────┤
│  引擎层 (Engine)                         │
│  V1: DynamicThinkingEngine               │
│  V2: + CanvasMind 内核                   │
│  V3: + Adapter 系统 + HEE                │
│  原则: 接口稳定，内部实现可演进            │
└─────────────────────────────────────────┘
```

## 项目结构

```
blueclaw/                          # 后端
├── api/                           # API 模块
│   ├── __init__.py               # 模块导出
│   ├── message_protocol.py       # 消息协议 (版本化)
│   ├── engine_facade.py          # 引擎外观
│   └── websocket_server.py       # WebSocket 服务
├── core/                          # 核心引擎
│   ├── dynamic_thinking_engine.py
│   └── execution_blueprint.py
└── ...

blueclaw-ui/                       # 前端
├── src/
│   ├── core/                      # 核心层 (不依赖渲染)
│   │   ├── protocol/
│   │   │   └── messageTypes.ts   # 消息协议定义
│   │   ├── engine/
│   │   │   └── BlueclawEngine.ts # WebSocket 客户端
│   │   └── state/
│   │       └── BlueprintStore.ts # 状态管理 (Zustand)
│   ├── adapters/                  # 渲染适配器
│   │   ├── BlueprintRenderer.ts  # 渲染器接口
│   │   ├── reactflow/            # V1: ReactFlow 实现
│   │   │   ├── ReactFlowAdapter.ts
│   │   │   └── components/
│   │   │       ├── ThinkingNode.tsx
│   │   │       ├── ExecutionNode.tsx
│   │   │       └── InterventionNode.tsx
│   │   └── canvasmind/           # V2: CanvasMind 实现 (占位)
│   │       └── CanvasMindAdapter.ts
│   └── app/
│       └── App.tsx               # 主应用组件
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## 核心设计

### 1. 协议层 (Protocol Layer)

**文件**: `blueclaw/api/message_protocol.py` (Python) / `blueclaw-ui/src/core/protocol/messageTypes.ts` (TypeScript)

**核心特性**:
- 版本化消息格式 (`PROTOCOL_VERSION = "1.0.0"`)
- 所有消息包含 `version`, `type`, `payload`, `timestamp`, `message_id`
- 版本兼容性检查

**消息类型**:
```typescript
enum MessageType {
  // Client -> Server
  TASK_START = 'task.start',
  THINKING_SELECT_OPTION = 'thinking.select_option',
  EXECUTION_INTERVENE = 'execution.intervene',
  
  // Server -> Client
  THINKING_NODE_CREATED = 'thinking.node_created',
  EXECUTION_BLUEPRINT_LOADED = 'execution.blueprint_loaded',
  EXECUTION_STEP_STARTED = 'execution.step_started',
  EXECUTION_STEP_COMPLETED = 'execution.step_completed',
  EXECUTION_INTERVENTION_NEEDED = 'execution.intervention_needed',
  EXECUTION_COMPLETED = 'execution.completed',
  
  // System
  ERROR = 'system.error',
  PING = 'system.ping',
  PONG = 'system.pong',
}
```

### 2. 引擎层 (Engine Layer)

**文件**: `blueclaw/api/engine_facade.py`

**设计原则**:
- 外观模式封装内部实现
- 接口稳定，内部可演进
- 支持 V1/V2/V3 引擎无缝切换

**核心接口**:
```python
class BlueclawEngineFacade:
    def process(self, user_input: str) -> ThinkingResultData
    def select_option(self, node_id: str, option_id: str) -> ThinkingResultData
    def provide_clarification(self, node_id: str, answer: str) -> ThinkingResultData
    def intervene(self, step_id: str, action_type: str, custom_input: Optional[str]) -> ReplanResult
    def pause_execution(self) -> None
    def resume_execution(self) -> None
```

### 3. 表现层 (Presentation Layer)

**文件**: `blueclaw-ui/src/adapters/BlueprintRenderer.ts`

**渲染器接口**:
```typescript
interface BlueprintRenderer {
  // 生命周期
  initialize(container: HTMLElement): void;
  destroy(): void;
  
  // 思考节点
  addThinkingNode(node: ThinkingNodeData): void;
  updateThinkingNode(nodeId: string, updates: Partial<ThinkingNodeData>): void;
  selectThinkingOption(nodeId: string, optionId: string): void;
  
  // 执行步骤
  addExecutionStep(step: ExecutionStepData): void;
  updateExecutionStep(stepId: string, updates: Partial<ExecutionStepData>): void;
  setStepStatus(stepId: string, status: NodeStatus): void;
  
  // 干预
  showInterventionPanel(stepId: string, actions: InterventionActionData[]): void;
  hideInterventionPanel(): void;
  
  // 视图
  focusOnNode(nodeId: string): void;
  fitView(): void;
}
```

**渲染器工厂**:
```typescript
// 注册渲染器
registerRenderer('reactflow', { create: (config) => new ReactFlowAdapter(config) });
registerRenderer('canvasmind', { create: (config) => new CanvasMindAdapter(config) });

// 创建渲染器 (运行时切换)
const renderer = createRenderer({ type: 'reactflow', container });
// 未来切换到 CanvasMind:
// const renderer = createRenderer({ type: 'canvasmind', container });
```

## 数据流

```
用户输入
    ↓
┌─────────────────────────────────────────┐
│ App.tsx                                 │
│ - 收集用户输入                          │
│ - 调用 engine.startTask()               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ BlueclawEngine (WebSocket 客户端)       │
│ - 发送 MessageFactory.createTaskStart() │
│ - 接收服务器消息                        │
└─────────────────────────────────────────┘
    ↓ WebSocket
┌─────────────────────────────────────────┐
│ BlueclawWebSocketServer (后端)          │
│ - 路由消息到 ConnectionHandler          │
│ - 调用 BlueclawEngineFacade             │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ BlueclawEngineFacade (引擎外观)         │
│ - 调用 DynamicThinkingEngine            │
│ - 调用 ExecutionBlueprintSystem         │
└─────────────────────────────────────────┘
    ↓
消息返回前端 → BlueprintStore (状态更新) → ReactFlowAdapter (渲染更新)
```

## 使用指南

### 启动后端服务器

```bash
# 启动 WebSocket 服务器
python start_websocket_server.py

# 或指定参数
python start_websocket_server.py --host 0.0.0.0 --port 8765
```

### 启动前端开发服务器

```bash
cd blueclaw-ui
npm install
npm run dev
```

前端将在 http://localhost:3000 启动

### 验证架构

```bash
python week15_5_verification.py
```

## 迁移指南

### 从 ReactFlow (V1) 迁移到 CanvasMind (V2)

**步骤 1**: 更新渲染器类型
```typescript
// App.tsx
const [rendererType, setRendererType] = useState<RendererType>('canvasmind');
```

**步骤 2**: 实现 CanvasMindAdapter (替换占位实现)
```typescript
// blueclaw-ui/src/adapters/canvasmind/CanvasMindAdapter.ts
// TODO: 集成 CanvasMind 引擎
```

**业务逻辑无需修改** - 接口保持一致！

## 验证标准

- [x] 消息格式包含 `version` 字段
- [x] 切换渲染器类型代码能跑（通过工厂模式）
- [x] 业务逻辑不直接依赖 ReactFlow API

## 文件清单

| 路径 | 描述 |
|------|------|
| `blueclaw/api/message_protocol.py` | 后端消息协议定义 |
| `blueclaw/api/engine_facade.py` | 引擎外观层 |
| `blueclaw/api/websocket_server.py` | WebSocket 服务器 |
| `blueclaw-ui/src/core/protocol/messageTypes.ts` | 前端消息协议定义 |
| `blueclaw-ui/src/core/engine/BlueclawEngine.ts` | WebSocket 客户端 |
| `blueclaw-ui/src/core/state/BlueprintStore.ts` | Zustand 状态管理 |
| `blueclaw-ui/src/adapters/BlueprintRenderer.ts` | 渲染器接口 |
| `blueclaw-ui/src/adapters/reactflow/ReactFlowAdapter.ts` | ReactFlow 实现 |
| `blueclaw-ui/src/adapters/canvasmind/CanvasMindAdapter.ts` | CanvasMind 占位 |
| `start_websocket_server.py` | 服务器启动脚本 |
| `week15_5_verification.py` | 架构验证测试 |
