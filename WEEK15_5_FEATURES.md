# Week 15.5 - 功能模块梳理与下一步开发指南

本文档梳理了 Week 15.5 架构之外的所有功能模块，便于下一步开发参考。

---

## 目录

1. [核心功能模块](#核心功能模块)
2. [Skill 系统](#skill-系统)
3. [Memory 系统](#memory-系统)
4. [Coordinator 集成层](#coordinator-集成层)
5. [GUI 实现](#gui-实现)
6. [测试工具](#测试工具)
7. [下一步开发计划](#下一步开发计划)

---

## 核心功能模块

### 1. 动态思考引擎 (Dynamic Thinking Engine)

**文件**: `blueclaw/core/dynamic_thinking_engine.py`

**功能**: 理解用户意图，生成思考节点和执行方案

**核心能力**:
```python
class DynamicThinkingEngine:
    def process(user_input: str, context: Optional[Dict] = None) -> ThinkingResult
        # 80%场景0-1次选择目标：
        # - 高置信度(>0.85): 直接生成执行预览
        # - 中置信度+探索性: 1轮澄清问题
        # - 低置信度: 带默认值的选项
    
    def continue_with_option(option_id: str, option: ThinkingOption) -> ThinkingResult
        # 用户选择选项后继续思考
    
    def continue_with_clarification(answer: str, question: ClarificationQuestion) -> ThinkingResult
        # 用户提供澄清回答后继续
```

**意图识别类型**:
- `travel_planning` - 旅行规划
- `code_generation` - 代码生成
- `data_analysis` - 数据分析
- `file_operation` - 文件操作
- `content_creation` - 内容创作
- `project_setup` - 项目搭建
- `general_task` - 通用任务

**当前状态**: ✅ 已实现基础版本，可识别简单意图

**下一步**: 接入 LLM API (OpenAI/Claude) 提升理解能力

---

### 2. 执行蓝图系统 (Execution Blueprint System)

**文件**: `blueclaw/core/execution_blueprint.py`

**功能**: 管理执行流程，支持可视化、暂停、干预、REPLAN

**核心能力**:
```python
class ExecutionBlueprintSystem:
    def load_blueprint(steps_data: List[Dict]) -> List[ExecutionStep]
        # 加载执行步骤
    
    async def execute_all() -> ExecutionResult
        # 执行所有步骤
    
    def pause_execution() -> None
        # 暂停执行
    
    def resume_execution() -> None
        # 恢复执行
    
    def skip_current_step() -> None
        # 跳过当前步骤
    
    def replan_from_step(step_index: int, new_steps: List[Dict]) -> None
        # 从指定步骤重新规划
```

**步骤状态**: PENDING -> RUNNING -> COMPLETED/FAILED/SKIPPED

**当前状态**: ✅ 已实现，支持基础执行流程控制

**下一步**: 接入真实的 Skill 执行

---

### 3. 思考选项系统 (Thinking Options)

**文件**: `blueclaw/core/thinking_options.py`

**功能**: 四选一交互模式

**核心能力**:
```python
class ThinkingBlueprintEngine:
    def analyze(user_input: str) -> ThinkingBlueprintResult
        # 分析用户输入，生成思考蓝图
        # 返回：意图识别、思考步骤、四选一选项
```

**意图类型**:
- CREATE - 创建
- MODIFY - 修改
- QUERY - 查询
- EXECUTE - 执行
- CHAT - 闲聊
- HELP - 帮助

**当前状态**: ⚠️ 独立模块，未完全集成到主流程

**下一步**: 与 DynamicThinkingEngine 合并或统一接口

---

## Skill 系统

### 架构

```
blueclaw/skills/
├── base_skill.py       # 基础 Skill 类
├── skill_registry.py   # Skill 注册中心
├── file_skill.py       # 文件操作
├── shell_skill.py      # Shell 命令
├── code_skill.py       # 代码执行
├── search_skill.py      # 网络搜索
└── browser_skill.py    # 浏览器自动化
```

### 基础 Skill 类

**文件**: `blueclaw/skills/base_skill.py`

```python
class BaseSkill(ABC):
    name: str                    # Skill 名称
    description: str             # 描述
    version: str = "1.0.0"       # 版本
    permission_level: PermissionLevel  # 权限级别
    requires_confirmation: bool  # 是否需要确认
    timeout: float = 60.0        # 超时时间
    
    @abstractmethod
    async def execute(self, **kwargs) -> SkillResult
        # 子类必须实现
    
    async def run(self, **kwargs) -> SkillResult
        # 包装 execute，添加验证、确认、超时控制
```

**权限级别**:
- `READ_ONLY` - 只读
- `WRITE` - 写入
- `DESTRUCTIVE` - 破坏性操作（删除等）
- `SYSTEM` - 系统级操作

### 已实现的 Skills

#### 1. FileSkill - 文件操作

**功能**: 文件读写、目录列表、文件删除

```python
# 读取文件
result = await skill_registry.execute('file', 
    operation='read', 
    path='data.json'
)

# 写入文件
result = await skill_registry.execute('file',
    operation='write',
    path='output.txt',
    content='Hello World'
)

# 列出目录
result = await skill_registry.execute('file',
    operation='list',
    path='./documents'
)
```

**支持格式**: 文本、JSON（自动解析）、CSV（自动解析）

**当前状态**: ✅ 已实现基础版本

#### 2. ShellSkill - Shell 命令

**功能**: 执行终端命令

```python
result = await skill_registry.execute('shell',
    command='ls -la',
    cwd='./project'
)
```

**安全限制**: 只读命令默认允许，写入/删除需要确认

**当前状态**: ✅ 已实现基础版本

#### 3. CodeSkill - 代码执行

**功能**: 执行 Python 代码

```python
result = await skill_registry.execute('code',
    code='print(2+2)',
    timeout=5.0
)
```

**当前状态**: ✅ 已实现基础版本

#### 4. SearchSkill - 网络搜索

**功能**: 网页搜索（模拟实现）

```python
result = await skill_registry.execute('search',
    query='Python asyncio tutorial'
)
```

**当前状态**: ⚠️ 占位实现，需接入真实搜索引擎

#### 5. BrowserSkill - 浏览器自动化

**功能**: 浏览器控制（模拟实现）

```python
result = await skill_registry.execute('browser',
    url='https://example.com',
    action='visit'
)
```

**当前状态**: ⚠️ 占位实现，需接入 Playwright/Selenium

### Skill 注册中心

**文件**: `blueclaw/skills/skill_registry.py`

**功能**: 统一管理所有 Skills

```python
from blueclaw.skills import SkillRegistry

registry = SkillRegistry()

# 列出所有 skills
skills = registry.list_skills()
# ['file', 'shell', 'code', 'search', 'browser']

# 执行 skill
result = await registry.execute('file', operation='read', path='test.txt')

# 获取 skill schema
schema = registry.get('file').to_schema()

# 根据任务描述自动选择 skill
skill = registry.get_skill_for_task("列出当前目录的文件")
# 返回 FileSkill 实例
```

**自动匹配关键词**:
- file: file, read, write, save, load, folder, directory
- shell: shell, command, terminal, bash, run, execute
- code: code, python, script, program, function
- search: search, find, google, lookup, query
- browser: browse, web, url, click, page, website

---

## Memory 系统

### 架构

```
blueclaw/memory/
├── memory_manager.py      # 统一接口
├── working_memory.py      # 工作记忆
└── long_term_memory.py    # 长期记忆
```

### MemoryManager - 统一接口

**文件**: `blueclaw/memory/memory_manager.py`

```python
class MemoryManager:
    async def add_message(role: str, content: str, **metadata)
        # 添加对话消息，自动提取实体
    
    async def add_experience(content: Any, persist: bool = True, **metadata)
        # 添加执行经验
    
    async def search_relevant(query: str, k: int = 5) -> List[Any]
        # 搜索相关记忆
    
    def add_entity(entity_type: str, name: str, properties: Dict)
        # 添加实体（邮箱、URL等）
    
    def get_context_string() -> str
        # 获取上下文字符串（用于 LLM 提示）
```

**自动实体提取**:
- 邮箱: `xxx@example.com`
- URL: `https://example.com`

**当前状态**: ⚠️ 基础实现，需接入向量数据库实现语义搜索

### WorkingMemory - 工作记忆

**功能**: 当前会话的短期记忆

```python
class WorkingMemory:
    def add_message(role: str, content: str, **metadata)
    def add_execution_result(step: str, result: Any, success: bool, **metadata)
    def set_goal(goal: str)
    def set_plan(plan: Dict)
    def get_context_string() -> str
```

### LongTermMemory - 长期记忆

**功能**: 持久化存储历史经验

```python
class LongTermMemory:
    def add_experience(content: Any, tags: List[str] = None) -> str
    def add_entity(entity_type: str, name: str, properties: Dict)
    def search_similar(query: str, k: int = 5) -> List[Any]
```

**当前状态**: ⚠️ 简单字典存储，需接入 SQLite/ChromaDB

---

## Coordinator 集成层

### ApplicationCoordinatorV3

**文件**: `blueclaw/integration/coordinator_v3.py`

**功能**: 整合思考引擎、执行蓝图、Skill、Memory 的协调器

**架构**:
```
ApplicationCoordinatorV3
├── DynamicThinkingEngine (思考)
├── ExecutionBlueprintSystem (执行)
├── SkillRegistry (技能)
├── MemoryManager (记忆)
└── ApplicationState (状态)
```

**核心流程**:
```python
coordinator = ApplicationCoordinatorV3(task_id="task-001")

# 设置回调（更新 UI）
coordinator.set_callbacks(
    on_state_change=lambda state: update_ui(state),
    on_blueprint_loaded=lambda steps: show_blueprint(steps),
    on_step_update=lambda step_id, status, index: update_step(step_id, status),
    on_execution_complete=lambda result: show_result(result),
)

# 启动任务
await coordinator.start_task("规划一个周末旅行")

# 处理用户响应
await coordinator.handle_user_response("选项A", "option_selection")

# 干预
await coordinator.handle_intervention("replan")
```

**当前状态**: ✅ 已实现，但使用 mock 执行

**下一步**: 接入真实的 Skill 执行和 LLM 思考

---

## GUI 实现

### 现有 GUI 版本

| 文件 | 特点 | 状态 |
|------|------|------|
| `blueclaw_v1_gui.py` | 基础三栏布局（聊天/画布/日志） | ✅ 可用 |
| `blueclaw_v1_gui_fixed.py` | 修复版本 | ✅ 可用 |
| `blueclaw_v1_gui_thinking.py` | 带思考过程展示 | ⚠️ 实验性 |
| `blueclaw_v1_gui_with_thinking.py` | 完整思考展示 | ⚠️ 实验性 |

### 启动 GUI

```bash
python blueclaw_v1_gui.py
```

**界面布局**:
```
+-----------+-------------------+-----------+
|  Chat     |     Canvas        |   Log     |
|  (30%)    |     (50%)         |   (20%)   |
|           |                   |           |
|  - Input  |  - Steps          |  - Status |
|  - History|  - Progress       |  - Debug  |
|  - Quick  |  - Visualization  |  - Errors |
+-----------+-------------------+-----------+
```

**功能**:
- 聊天交互
- 执行蓝图可视化
- 暂停/继续按钮
- 重新规划按钮
- 进度条显示

**当前状态**: ✅ PyQt5 实现，功能完整

**下一步**: 迁移到 Web 前端（ReactFlow），或使用 PyQt WebEngine 嵌入

---

## 测试工具

### 测试文件清单

| 文件 | 用途 | 状态 |
|------|------|------|
| `simple_1minute_test.py` | 1分钟架构测试 | ✅ 推荐 |
| `week15_5_verification.py` | 架构验证 | ✅ 可用 |
| `demo_architecture.py` | 架构演示 | ✅ 可用 |
| `test_websocket_client.py` | WebSocket 客户端测试 | ✅ 可用 |
| `test_thinking_engine.py` | 思考引擎测试 | ⚠️ 需更新 |
| `test_integration.py` | 集成测试 | ⚠️ 需更新 |
| `test_scenario.py` | 场景测试 | ⚠️ 需更新 |
| `test_startup.py` | 启动测试 | ⚠️ 需更新 |

### 推荐的测试流程

```bash
# 1. 架构测试（必做）
python simple_1minute_test.py

# 2. 手动测试 WebSocket
python start_websocket_server.py
# 另开终端
python test_websocket_client.py

# 3. GUI 测试
python blueclaw_v1_gui.py
```

---

## 下一步开发计划

### Phase 1: 核心功能打通（优先级：高）

#### 1.1 接入 LLM 思考引擎

**目标**: 替换简单的意图识别，使用真实 LLM

**文件**: `blueclaw/core/dynamic_thinking_engine.py`

**修改点**:
```python
class DynamicThinkingEngine:
    def __init__(self):
        self.llm_client = OpenAIClient()  # 新增
    
    def process(self, user_input: str, context: Optional[Dict] = None) -> ThinkingResult:
        # 当前：简单关键词匹配
        # 目标：调用 LLM API 生成思考结果
        response = self.llm_client.chat.completions.create(
            model="gpt-4",
            messages=[...],
            tools=[...]  # function calling
        )
```

**依赖**: OpenAI/Anthropic API Key

#### 1.2 接入真实 Skill 执行

**目标**: 让 ExecutionBlueprintSystem 真正执行 Skills

**文件**: `blueclaw/core/execution_blueprint.py`

**修改点**:
```python
async def _execute_step(self, step: ExecutionStep) -> bool:
    # 当前：模拟执行
    await asyncio.sleep(0.5)
    step.result = "Mock result"
    
    # 目标：调用 SkillRegistry 执行
    skill_result = await self.skill_registry.execute(
        skill_name=step.skill_name,
        **step.parameters
    )
    step.result = skill_result.data
    return skill_result.success
```

#### 1.3 完善 Skill 实现

**优先级**:
1. FileSkill - 已可用，增强错误处理
2. ShellSkill - 已可用，添加安全限制
3. CodeSkill - 已可用，添加沙箱执行
4. SearchSkill - 接入真实搜索引擎
5. BrowserSkill - 接入 Playwright

### Phase 2: Memory 系统增强（优先级：中）

#### 2.1 接入向量数据库

**目标**: 实现语义搜索

**选项**:
- ChromaDB - 轻量，嵌入使用
- SQLite + sqlite-vec - 简单
- Pinecone - 云端

**修改点**:
```python
class LongTermMemory:
    def __init__(self):
        self.vector_db = ChromaDB()  # 替换简单字典
    
    def add_experience(self, content: Any, tags: List[str] = None):
        embedding = self.embed(content)
        self.vector_db.add(id, content, embedding, tags)
    
    def search_similar(self, query: str, k: int = 5):
        query_embedding = self.embed(query)
        return self.vector_db.search(query_embedding, k)
```

#### 2.2 实体关系图谱

**目标**: 建立实体间关系，支持复杂查询

```python
# 示例：用户提到"我的邮箱是 a@b.com"
memory.add_entity('email', 'a@b.com', {'owner': 'user'})

# 后续查询"给我邮箱发邮件"
# 系统知道使用 a@b.com
```

### Phase 3: 前端完善（优先级：中）

#### 3.1 ReactFlow 前端完成

**文件**: `blueclaw-ui/src/`

**待完成**:
- [ ] 用户输入界面
- [ ] 选项选择 UI
- [ ] 执行步骤动画
- [ ] 干预面板
- [ ] 错误处理提示

#### 3.2 美观优化

- [ ] 节点样式设计
- [ ] 连线动画
- [ ] 主题切换（暗黑/明亮）
- [ ] 响应式布局

### Phase 4: 高级功能（优先级：低）

#### 4.1 多轮对话优化

- 对话历史压缩
- 长期记忆召回
- 上下文窗口管理

#### 4.2 协作模式

- 多用户同时查看画布
- 操作权限控制
- 实时同步

#### 4.3 CanvasMind 迁移准备

- 完成 CanvasMindAdapter 实现
- 性能测试对比
- 渐进式迁移方案

---

## 开发建议

### 代码规范

1. **接口优先**: 所有模块先定义接口，再实现
2. **向后兼容**: 新功能不能破坏现有接口
3. **测试覆盖**: 每个新功能必须带测试
4. **文档同步**: 代码修改时同步更新本文档

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查消息流
from blueclaw.api import MessageFactory
msg = MessageFactory.create_task_start("测试")
print(msg.to_json())  # 查看消息格式

# 测试单个 skill
from blueclaw.skills import SkillRegistry
registry = SkillRegistry()
result = await registry.execute('file', operation='list', path='.')
print(result)
```

### 常见问题

**Q: Skill 执行失败如何调试？**
A: 检查 `SkillResult.error` 字段，启用 `BaseSkill` 的详细日志

**Q: Memory 搜索不到相关内容？**
A: 当前是简单关键词匹配，需等待向量数据库接入

**Q: 如何添加新的 Skill？**
A: 继承 `BaseSkill`，实现 `execute` 方法，注册到 `SkillRegistry`

---

## 总结

| 模块 | 当前状态 | 下一步 |
|------|----------|--------|
| 思考引擎 | 基础实现 | 接入 LLM |
| 执行蓝图 | 可用 | 接入 Skill 执行 |
| Skill 系统 | 3/5 可用 | 完善 Search/Browser |
| Memory | 基础实现 | 接入向量数据库 |
| Coordinator | 可用 | 整合上述改进 |
| GUI | PyQt 可用 | 完成 ReactFlow 前端 |

**推荐开发顺序**:
1. 接入 LLM 思考引擎（核心）
2. Skill 执行打通（核心）
3. 完善 ReactFlow 前端（用户体验）
4. Memory 增强（进阶功能）
5. CanvasMind 迁移（未来）
