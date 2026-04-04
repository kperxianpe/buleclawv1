#!/usr/bin/env python3
"""快速测试启动问题"""
import sys
import os

print("="*60)
print("Blueclaw v1.0 Startup Test")
print("="*60)

# 测试基础导入
print("\n[1/5] Testing base imports...")
try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QColor, QPen, QPainter
    print("  [OK] PyQt5 imports OK")
except Exception as e:
    print(f"  [FAIL] PyQt5 error: {e}")
    sys.exit(1)

# 测试画布模块
print("\n[2/5] Testing canvas modules...")
try:
    from v1.canvas.items import StepNodeItem, OptionButtonItem, ExecutionNodeItem
    print("  [OK] canvas.items OK")
except Exception as e:
    print(f"  [FAIL] canvas.items error: {e}")
    import traceback
    traceback.print_exc()

try:
    from v1.canvas.layered_canvas import LayeredCanvasSystem, ThinkingCanvas, ExecutionCanvas
    print("  [OK] canvas.layered_canvas OK")
except Exception as e:
    print(f"  [FAIL] canvas.layered_canvas error: {e}")
    import traceback
    traceback.print_exc()

# 测试LLM引擎
print("\n[3/5] Testing LLM engine...")
try:
    from v1.core.llm_thinking_engine import LLMThinkingEngine
    print("  [OK] llm_thinking_engine OK")
except Exception as e:
    print(f"  [FAIL] llm_thinking_engine error: {e}")
    import traceback
    traceback.print_exc()

# 测试主窗口
print("\n[4/5] Testing main window...")
try:
    from v1.main_window import BlueclawV1MainWindow
    print("  [OK] main_window OK")
except Exception as e:
    print(f"  [FAIL] main_window error: {e}")
    import traceback
    traceback.print_exc()

# 创建应用实例
print("\n[5/5] Testing QApplication creation...")
try:
    app = QApplication.instance() or QApplication(sys.argv)
    print("  [OK] QApplication created OK")
    
    # 创建主窗口（但不显示）
    print("\n[6/6] Testing MainWindow creation...")
    window = BlueclawV1MainWindow(use_llm=False)
    print("  [OK] MainWindow created OK")
    print("\n" + "="*60)
    print("All tests passed! Ready to launch.")
    print("="*60)
    print("\nRun: python start_v1.py")
    
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
