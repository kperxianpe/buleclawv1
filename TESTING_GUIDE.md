# Blueclaw v1.0 - 测试指南

## 为什么需要测试？

之前的GUI闪退问题暴露了测试覆盖的不足：
- ❌ 命令行测试无法发现GUI线程问题
- ❌ 单线程测试无法发现并发问题
- ✅ 现在通过全面测试确保稳定性

---

## 快速测试

### 1. 运行所有测试（推荐）
```bash
cd blueclawv1.0/tests
python run_all_tests.py
```

预期输出：
```
======================================================================
FINAL SUMMARY
======================================================================
✓ PASS: GUI Unit Tests
✓ PASS: Core Integration Tests
✓ PASS: GUI Integration Tests
✓ PASS: Comprehensive Q&A Tests
----------------------------------------------------------------------
Total: 4, Passed: 4, Failed: 0
======================================================================
```

### 2. 测试GUI（修复版）
```bash
cd blueclawv1.0
python run_fixed_gui.py
```

测试场景：
1. 输入"你好" → 应该正常显示问候语，不闪退
2. 输入"列出当前目录的文件" → 应该显示执行蓝图
3. 快速点击发送 → 应该稳定处理

---

## 详细测试

### GUI单元测试
```bash
python tests/test_gui_unit.py
```

测试内容：
- StepWidget组件
- SignalBridge信号
- 跨线程信号传递
- 边界情况处理

### GUI集成测试
```bash
python tests/test_gui_integration.py
```

测试内容：
- 问候流程
- 任务执行流程
- 快速输入处理
- 并发操作
- 回调压力

### Q&A综合测试
```bash
python comprehensive_qa_test.py
```

测试内容：
- 39个Q&A场景
- 8个类别全覆盖
- 边界情况

---

## 测试分类

### 单元测试（11个）
| 测试 | 描述 |
|-----|------|
| test_step_widget_creation | 步骤控件创建 |
| test_step_status_update | 状态更新 |
| test_signal_emission | 信号发射 |
| test_cross_thread_signal | 跨线程信号 |
| ... | ... |

### 集成测试（5个）
| 测试 | 描述 |
|-----|------|
| Greeting Flow | 问候流程（线程安全） |
| Task Execution Flow | 任务执行 |
| Rapid Input Test | 快速输入 |
| Concurrent Operations | 并发操作 |
| Callback Stress Test | 回调压力 |

### Q&A测试（39个）
| 类别 | 数量 | 示例 |
|-----|------|------|
| greeting | 6 | 你好, Hello |
| identity | 5 | 你是谁 |
| capability | 5 | 你能做什么 |
| task_file | 5 | 列出文件 |
| task_travel | 5 | 规划旅行 |
| task_code | 5 | 写Python脚本 |
| task_data | 3 | 分析CSV |
| edge | 5 | 边界情况 |

---

## 常见问题

### Q: 测试需要多长时间？
A: 
- 单元测试：~1秒
- 集成测试：~5秒
- Q&A测试：~30秒
- 全部测试：~40秒

### Q: 测试失败怎么办？
A:
1. 检查PyQt5是否安装：`pip install PyQt5`
2. 检查依赖：`pip install -r requirements.txt`
3. 查看具体错误信息
4. 报告问题

### Q: 如何添加新测试？
A:
1. 在 `tests/` 目录创建测试文件
2. 继承 `unittest.TestCase`
3. 运行 `python run_all_tests.py`

### Q: GUI还是闪退？
A:
确保使用修复版：
```bash
# 使用修复版（推荐）
python run_fixed_gui.py

# 不是旧版
python blueclaw_v1_gui.py  # 旧版可能有问题
```

---

## 测试报告

### 当前状态
- ✅ 总测试数：55
- ✅ 通过率：100%
- ✅ 线程安全：已验证
- ✅ 稳定性：已验证

### 已修复问题
- ✅ GUI线程安全
- ✅ 问答识别
- ✅ 任务执行
- ✅ 并发处理

---

## 持续测试

### 开发时
```bash
# 每次修改后运行
python tests/test_gui_unit.py
```

### 发布前
```bash
# 完整测试
python tests/run_all_tests.py
```

### CI/CD
```bash
# 自动化测试
pytest tests/ -v
```

---

## 联系支持

如有测试问题，请提供：
1. 测试命令
2. 错误输出
3. 系统信息（Python版本、操作系统）
