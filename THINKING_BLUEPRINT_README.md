# Blueclaw v1.0 - Thinking Blueprint (思考蓝图)

## 概述

Thinking Blueprint（思考蓝图）是 Blueclaw v1.0 的核心创新功能，为用户提供了 **四选项交互模式（Four-Option Mode）**，使 AI 能够更智能地理解用户意图并提供精确的交互选项。

## 核心特性

### 1. 意图识别 (Intent Recognition)

系统自动分析用户输入，识别以下意图类型：

| 意图类型 | 描述 | 示例 |
|---------|------|------|
| CREATE | 创建/生成内容 | "创建一个游戏" |
| MODIFY | 修改/更新内容 | "修改这个文件" |
| QUESTION | 提问 | "今天天气怎么样？" |
| CHAT | 闲聊 | "你好" |
| EXECUTE | 执行命令 | "运行脚本" |
| ANALYZE | 分析内容 | "分析这个代码" |
| UNKNOWN | 未知意图 | 其他输入 |

### 2. 思考过程可视化 (Thinking Steps)

系统会展示 AI 的思考过程：

```
Step 1: Intent Analysis
   识别用户意图: create

Step 2: Requirements Analysis  
   从输入中提取创建需求...

Step 3: Context Analysis
   分析对话历史...

Step 4: Generate Options
   基于意图 'create' 生成4个选项...
```

### 3. 四选项交互模式 (Four-Option Mode)

根据识别到的意图，系统会动态生成 4 个选项供用户选择：

**CREATE 模式选项：**
- **[A] Quick Template** - 使用预建模板快速开始 (90%)
- **[B] Custom Creation** - 从头开始完全定制 (85%)
- **[C] View Examples** - 先查看类似示例 (70%)
- **[D] AI Recommendation** - 让AI推荐最佳方案 (75%)

**QUESTION 模式选项：**
- **[A] Quick Answer** - 给出简洁直接答案 (95%)
- **[B] Detailed Explanation** - 提供详细解释 (85%)
- **[C] Search Online** - 搜索最新信息 (75%)
- **[D] Related Resources** - 显示相关学习资源 (70%)

每个选项都显示：
- 标签 (A/B/C/D)
- 图标
- 标题
- 描述
- 置信度百分比
- 可视化置信度条

### 4. 执行流程

```
用户输入 → 意图识别 → 思考过程 → 四选项展示 → 用户选择 → 执行
```

## 文件结构

```
blueclawv1.0/
├── core/
│   ├── __init__.py                 # 核心模块初始化
│   ├── thinking_engine.py          # 思考引擎核心
│   └── thinking_widgets.py         # PyQt5 UI组件
├── blueclaw_v1_gui_with_thinking.py # 集成GUI主文件
├── start_blueclaw_v1.py            # 启动脚本
├── test_integration.py             # 集成测试
└── THINKING_BLUEPRINT_README.md    # 本文档
```

## 启动方法

### 方法1: 使用启动脚本
```bash
python start_blueclaw_v1.py
```

### 方法2: 直接运行GUI
```bash
python blueclaw_v1_gui_with_thinking.py
```

## 界面布局

```
┌─────────────────┬───────────────────────────┬─────────────┐
│   Chat Panel    │      Canvas Panel         │ Vision/Log  │
│    (25%)        │         (55%)             │   (20%)     │
│                 │                           │             │
│  User messages  │  ┌─────────────────────┐  │  System     │
│  AI responses   │  │  Thinking Blueprint │  │  logs       │
│                 │  │  - Thinking steps   │  │             │
│  [Input box]    │  │  - 4-Option UI      │  │  [Progress] │
│  [Send button]  │  └─────────────────────┘  │             │
│                 │                           │             │
│                 │  [Switch View] [Pause]    │             │
└─────────────────┴───────────────────────────┴─────────────┘
```

## 使用流程示例

### 示例 1: 创建内容
```
用户: "帮我创建一个网络多人游戏"

系统:
[意图识别] CREATE (90%)

[思考过程]
Step 1: Intent Analysis - 识别用户意图: create
Step 2: Requirements Analysis - 从输入中提取创建需求
Step 3: Context Analysis - 分析对话历史
Step 4: Generate Options - 基于意图生成4个选项

[4-Option Mode]
[A] Quick Template (90%) █████████-
    使用预建模板快速开始
    
[B] Custom Creation (85%) ████████--
    从头开始完全定制
    
[C] View Examples (70%) ███████---
    先查看类似示例
    
[D] AI Recommendation (75%) ███████---
    让AI推荐最佳方案

用户选择 [A] → 系统执行 quick_template 动作
```

### 示例 2: 提问
```
用户: "Python的列表推导式怎么用？"

系统:
[意图识别] QUESTION (95%)

[4-Option Mode]
[A] Quick Answer (95%) █████████-
    给出简洁直接答案
    
[B] Detailed Explanation (85%) ████████--
    提供详细解释和示例
    
[C] Search Online (75%) ███████---
    搜索最新信息和最佳实践
    
[D] Related Resources (70%) ███████---
    显示相关学习资源
```

## 技术实现

### ThinkingEngine 核心类

```python
class ThinkingEngine:
    def analyze(self, user_input: str) -> ThinkingResult:
        """分析用户输入，返回意图、思考步骤和选项"""
        
    def _recognize_intent(self, text: str) -> Tuple[IntentType, float]:
        """识别意图并返回置信度"""
        
    def _generate_thinking_steps(self, intent: IntentType, ...) -> List[ThinkingStep]:
        """生成思考过程步骤"""
        
    def _generate_options(self, intent: IntentType, ...) -> List[ThinkingOption]:
        """生成四选项"""
        
    def execute_option(self, result: ThinkingResult, option_id: str) -> Dict:
        """执行选中的选项"""
```

### UI组件

- **StepWidget**: 显示单个思考步骤
- **OptionButton**: 四选项中的单个选项按钮
- **ThinkingBlueprintWidget**: 完整思考蓝图面板

## 测试

运行集成测试：
```bash
python test_integration.py
```

测试内容包括：
1. 思考引擎导入
2. 意图识别功能
3. PyQt5 UI组件
4. GUI集成
5. 完整工作流程

## 后续扩展

1. **动态选项生成** - 基于LLM动态生成选项
2. **学习用户偏好** - 根据历史选择优化选项排序
3. **多语言支持** - 扩展更多语言
4. **自定义选项模板** - 允许用户定义自己的选项模板

## 注意事项

- 当前使用英文UI（避免Windows控制台GBK编码问题）
- 支持中英文输入
- 需要 PyQt5 支持
- 需要 blueclaw 协调器模块
