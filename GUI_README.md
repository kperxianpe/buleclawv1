# Blueclaw v1.0 GUI 使用指南

## 启动方式

### 方式1: 桌面GUI (推荐)

基于 tkinter，无需额外安装：

```bash
python start_gui.py
```

界面布局：
- **左侧 (30%)**: 对话面板 - 与AI交互
- **中间 (50%)**: 执行蓝图 - 可视化执行流程
- **右侧 (20%)**: 日志面板 - 查看详细日志

### 方式2: Web界面

基于 Streamlit，更美观：

```bash
# 安装依赖
pip install streamlit

# 启动
streamlit run start_web.py
```

然后在浏览器打开 http://localhost:8501

## GUI功能说明

### 对话面板
- 输入任务描述
- 查看AI回复
- 快速任务按钮（规划旅行、列文件）

### 执行蓝图面板
- 实时显示执行步骤
- 步骤状态图标：
  - ⏳ 等待中
  - 🔄 执行中
  - ✅ 已完成
  - ❌ 失败
  - ⏸️ 已暂停

### 日志面板
- 查看详细执行日志
- 暂停/继续按钮
- 重置按钮

### 干预功能
当执行需要干预时，会弹出对话框询问是否回退到思考阶段。

## 示例任务

1. **规划旅行**: "我想规划一个周末短途旅行"
2. **文件操作**: "列出当前目录的文件"
3. **代码生成**: "写一个Python计算斐波那契数列的函数"
4. **数据分析**: "分析data.csv文件"

## 故障排除

### GUI无法启动

1. **检查Python版本**
   ```bash
   python --version  # 需要 3.7+
   ```

2. **检查tkinter**
   ```bash
   python -c "import tkinter"
   ```
   如果报错，需要安装tkinter：
   - Windows: 重新安装Python，勾选"tcl/tk"
   - Ubuntu: `sudo apt-get install python3-tk`
   - macOS: 自带

3. **使用命令行模式**
   ```bash
   python launch.py --mode console
   ```

### 界面显示异常

- 调整窗口大小至1200x700以上
- 确保系统字体支持中文（Microsoft YaHei）
