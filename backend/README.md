# Blueclaw V2 Backend - Week 18

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python main.py
```

服务将启动在 `ws://localhost:8000`

### 3. 测试连接

```bash
# 运行集成测试
python tests/test_websocket.py

# 或使用 wscat 手动测试
npm install -g wscat
wscat -c ws://localhost:8000
```

## 接口文档

### 客户端 → 服务端

| 消息类型 | 说明 | Payload |
|---------|------|---------|
| `task.start` | 开始新任务 | `{user_input: string}` |
| `thinking.select_option` | 选择思考选项 | `{task_id, node_id, option_id}` |
| `execution.start` | 开始执行 | `{task_id}` |
| `task.cancel` | 取消任务 | `{task_id}` |

### 服务端 → 客户端

| 消息类型 | 说明 | Payload |
|---------|------|---------|
| `task.created` | 任务创建成功 | `{task_id, status}` |
| `task.status_updated` | 状态更新 | `{status}` |
| `task.cancelled` | 任务取消 | `{reason}` |
| `thinking.node_selected` | 选项已选择 | `{selected_option}` |
| `execution.blueprint_loaded` | 蓝图加载 | `{steps}` |
| `error` | 错误信息 | `{message}` |

## 项目结构

```
backend/
├── websocket/
│   ├── __init__.py
│   ├── server.py          # WebSocket 服务
│   └── message_router.py  # 消息路由
├── core/
│   ├── __init__.py
│   ├── task_manager.py    # 任务管理
│   └── checkpoint.py      # 状态持久化
├── models/
│   ├── __init__.py
│   ├── task.py            # 任务模型
│   └── messages.py        # 消息类型
├── tests/
│   └── test_websocket.py  # 集成测试
├── checkpoints/           # 检查点存储目录
├── main.py                # 服务入口
├── requirements.txt       # 依赖
└── README.md              # 本文档
```

## 特性

- ✅ WebSocket 实时通信
- ✅ 任务生命周期管理
- ✅ 状态持久化（断线重连）
- ✅ 消息路由分发
- ✅ 多任务并发支持

## 前端对接示例

```javascript
// 1. 连接
const ws = new WebSocket('ws://localhost:8000');

// 2. 创建任务
ws.send(JSON.stringify({
  type: 'task.start',
  payload: { user_input: '任务描述' }
}));

// 3. 接收消息
ws.onmessage = (e) => {
  const data = JSON.parse(e.data);
  console.log('Received:', data.type, data.payload);
  
  if (data.type === 'task.created') {
    console.log('Task ID:', data.payload.task_id);
  }
};

// 4. 选择选项
ws.send(JSON.stringify({
  type: 'thinking.select_option',
  payload: { 
    task_id: 'task_xxx',
    node_id: 'node_1', 
    option_id: 'A' 
  }
}));

// 5. 断线重连
ws.onclose = () => {
  setTimeout(() => {
    ws = new WebSocket('ws://localhost:8000');
    // 任务状态会自动恢复
  }, 1000);
};
```

## 配置

### 修改端口

编辑 `main.py`:

```python
server = BlueclawWebSocketServer(host="localhost", port=8080)
```

### 检查点存储路径

编辑 `core/checkpoint.py`:

```python
checkpoint_manager = CheckpointManager(storage_dir="/path/to/checkpoints")
```

## 测试

```bash
# 启动服务
python main.py &

# 运行测试
python tests/test_websocket.py

# 预期输出:
# ============================================================
# WebSocket Integration Test
# ============================================================
# 
# [TEST 1] Create task
# [PASS] Task created: task_xxx
# 
# [TEST 2] Select option
# [PASS] Response type: thinking.node_selected
# 
# ...
# All tests passed!
```

## 调试

查看检查点文件:

```bash
ls checkpoints/
cat checkpoints/task_xxx.json
```

## 故障排查

| 问题 | 解决方案 |
|-----|---------|
| Connection refused | 确认服务已启动 (`python main.py`) |
| Module not found | 确认在 backend 目录下运行 |
| Port already in use | 修改端口或关闭占用端口的程序 |
| Permission denied | 检查 checkpoints 目录权限 |

## Week 19 预告

- 思考引擎集成（LLM 调用）
- 执行引擎集成（步骤调度）
- 消息推送与同步
- 完整思考-执行流程

---

*Week 18 完成 - 2026-04-06*
