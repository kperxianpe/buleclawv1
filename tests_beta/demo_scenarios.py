#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
demo_scenarios.py - Blueclaw v1.0 Beta Demo Scenarios

Beta 测试演示场景 - 验证端到端功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from v1.core.llm_thinking_engine import LLMThinkingEngine, create_llm_thinking_engine
from core.thinking_engine import ThinkingEngine


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    else:
        print(f"\n{'='*60}\n")


def demo_scenario_1_xiaohongshu():
    """
    场景 1：小红书创作
    
    测试：CREATE 意图 -> 四选项 -> 选择 -> 执行
    """
    print_separator("SCENARIO 1: Xiaohongshu Content Creation")
    
    engine = ThinkingEngine()
    
    user_input = "写一篇小红书，主题是夏日穿搭"
    print(f"User: {user_input}\n")
    
    # 思考分析
    result = engine.analyze(user_input)
    
    print(f"[Intent] {result.intent.value.upper()} ({result.intent_confidence:.0%})")
    print("\n[Thinking Steps]")
    for step in result.thinking_steps:
        print(f"  {step.step_number}. {step.title}: {step.description}")
    
    print("\n[4-Option Mode]")
    for opt in result.options:
        bar = "#" * int(opt.confidence / 10) + "-" * (10 - int(opt.confidence / 10))
        print(f"  [{opt.label}] {opt.title}")
        print(f"      {opt.description}")
        print(f"      Match: {bar} {opt.confidence}%")
    
    # 模拟选择
    if result.options:
        selected = result.options[0]
        print(f"\n[User Selection] [{selected.label}] {selected.title}")
        
        exec_result = engine.execute_option(result, selected.option_id)
        print(f"[Execution] Action: {exec_result['action']}")
        
    print("\n[Expected Flow]")
    print("  1. Thinking canvas embeds in chat")
    print("  2. User selects option A (Quick Template)")
    print("  3. Execution canvas shows: Search → Write → Format")
    print("  4. Each step visible with status updates")


def demo_scenario_2_file_organize():
    """
    场景 2：文件整理
    
    测试：EXECUTE 意图 -> 真实文件操作
    """
    print_separator("SCENARIO 2: Desktop File Organization")
    
    engine = ThinkingEngine()
    
    user_input = "整理桌面文件，按类型分类"
    print(f"User: {user_input}\n")
    
    result = engine.analyze(user_input)
    
    print(f"[Intent] {result.intent.value.upper()} ({result.intent_confidence:.0%})")
    
    print("\n[4-Option Mode]")
    for opt in result.options:
        print(f"  [{opt.label}] {opt.title} - {opt.description}")
    
    print("\n[Expected Flow]")
    print("  1. Confirm classification rules [By Type/Date/Project]")
    print("  2. Execution canvas shows:")
    print("     - Scan Desktop")
    print("     - Create Folders (Documents, Images, Archives)")
    print("     - Move Files")
    print("     - Generate Report")
    print("  3. Real file operations with progress")


def demo_scenario_3_code_generation():
    """
    场景 3：代码生成
    
    测试：CREATE 意图（代码）-> 多步骤执行
    """
    print_separator("SCENARIO 3: Python Web Scraper")
    
    engine = ThinkingEngine()
    
    user_input = "写一个 Python 爬虫抓取豆瓣电影 Top250"
    print(f"User: {user_input}\n")
    
    result = engine.analyze(user_input)
    
    print(f"[Intent] {result.intent.value.upper()} ({result.intent_confidence:.0%})")
    
    print("\n[Thinking Steps]")
    for step in result.thinking_steps:
        print(f"  {step.step_number}. {step.title}")
    
    print("\n[4-Option Mode]")
    for opt in result.options:
        print(f"  [{opt.label}] {opt.title}")
        print(f"      Confidence: {opt.confidence}%")
    
    print("\n[Expected Flow]")
    print("  1. Thinking canvas with 3 options:")
    print("     A. Quick Template (Basic requests)")
    print("     B. Advanced (With anti-detection)")
    print("     C. Clarify requirements")
    print("  2. Execution shows:")
    print("     - Analyze Website Structure")
    print("     - Generate Code")
    print("     - Test Run")
    print("     - Save to File")


def demo_llm_engine():
    """
    演示 LLM 思考引擎
    """
    print_separator("LLM Thinking Engine Demo (Mock Mode)")
    
    engine = create_llm_thinking_engine(use_mock=True)
    
    test_inputs = [
        "今天天气怎么样",
        "帮我写一个爬虫",
        "整理我的桌面文件",
    ]
    
    for user_input in test_inputs:
        print(f"\nUser: {user_input}")
        print("-" * 40)
        
        import asyncio
        result = asyncio.run(engine.analyze(user_input))
        
        print(f"  Intent: {result.intent.value} ({result.intent_confidence:.0%})")
        print(f"  Needs Blueprint: {result.context.get('needs_blueprint', True)}")
        print(f"  Options: {len(result.options)}")
        
        for opt in result.options[:2]:  # 只显示前2个
            print(f"    [{opt.label}] {opt.title} ({opt.confidence}%)")
            
    print("\n[Stats]", engine.get_stats())


def demo_position_awareness():
    """
    演示位置感知
    """
    print_separator("Canvas Position Awareness Demo")
    
    from PyQt5.QtWidgets import QApplication
    from v1.canvas.layered_canvas import LayeredCanvasSystem
    from v1.canvas.position_awareness import CanvasPositionAwareness
    from core.thinking_engine import ThinkingEngine
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 创建画布系统
    canvas_system = LayeredCanvasSystem()
    
    # 渲染一些内容
    engine = ThinkingEngine()
    result = engine.analyze("Create a website")
    
    # 渲染到思考画布
    canvas_system.embed_thinking_in_chat(result)
    
    # 位置感知
    awareness = CanvasPositionAwareness(canvas_system.get_thinking_canvas())
    
    # 扫描元素
    elements = awareness.scan_canvas_elements()
    
    print(f"[Scanned] Found {len(elements)} elements:")
    for e in elements:
        print(f"  - {e.element_type}: {e.text[:30] if e.text else 'N/A'}")
        print(f"    Position: ({e.position[0]:.0f}, {e.position[1]:.0f})")
        print(f"    Clickable: {e.is_clickable}")
    
    # 获取可点击按钮
    buttons = awareness.get_clickable_buttons()
    print(f"\n[Clickable Buttons] {len(buttons)} found")
    
    # 导出快照
    snapshot = awareness.export_layout_snapshot()
    print(f"\n[Layout Snapshot]")
    print(f"  Canvas Size: {snapshot.canvas_size}")
    print(f"  Elements: {len(snapshot.elements)}")
    print(f"  Timestamp: {snapshot.timestamp}")


def demo_persistence():
    """
    演示状态持久化
    """
    print_separator("State Persistence Demo")
    
    from persistence.state_manager import StatePersistenceManager, TaskStatus
    
    # 创建管理器（使用内存数据库）
    import tempfile
    db_path = os.path.join(tempfile.gettempdir(), "blueclaw_demo.db")
    
    if os.path.exists(db_path):
        os.remove(db_path)
    
    manager = StatePersistenceManager(db_path)
    
    # 保存任务
    print("[Save Task]")
    task_id = manager.save_task({
        'user_input': 'Test task for persistence',
        'intent': 'create',
        'status': TaskStatus.EXECUTING.value,
        'progress': 50,
        'thinking_blueprint': {'steps': [{'name': 'Step 1'}]},
        'execution_blueprint': {'steps': [{'name': 'Exec 1'}]}
    })
    print(f"  Task ID: {task_id}")
    
    # 加载任务
    print("\n[Load Task]")
    task = manager.load_task(task_id)
    print(f"  Input: {task['user_input']}")
    print(f"  Status: {task['status']}")
    print(f"  Progress: {task['progress']}%")
    
    # 创建检查点
    print("\n[Create Checkpoint]")
    cp_id = manager.create_checkpoint(task_id, 'executing', {
        'current_step': 2,
        'variables': {'x': 10}
    })
    print(f"  Checkpoint ID: {cp_id}")
    
    # 获取检查点
    checkpoint = manager.get_latest_checkpoint(task_id)
    print(f"  Latest: {checkpoint.phase} at {checkpoint.created_at}")
    
    # 更新状态
    print("\n[Update Status]")
    manager.update_task_status(task_id, TaskStatus.COMPLETED, 100)
    task = manager.load_task(task_id)
    print(f"  New Status: {task['status']}")
    
    # 获取统计
    print("\n[Statistics]")
    stats = manager.get_stats()
    print(f"  Total Tasks: {stats['total_tasks']}")
    print(f"  DB Size: {stats['database_size_bytes']} bytes")
    
    # 清理
    os.remove(db_path)


def run_all_demos():
    """运行所有演示"""
    print_separator("BLUECLAW V1.0 BETA DEMO SCENARIOS")
    print("Week 15 Implementation - Layered Canvas + LLM Engine")
    
    try:
        demo_scenario_1_xiaohongshu()
    except Exception as e:
        print(f"Scenario 1 Error: {e}")
    
    try:
        demo_scenario_2_file_organize()
    except Exception as e:
        print(f"Scenario 2 Error: {e}")
    
    try:
        demo_scenario_3_code_generation()
    except Exception as e:
        print(f"Scenario 3 Error: {e}")
    
    try:
        demo_llm_engine()
    except Exception as e:
        print(f"LLM Engine Error: {e}")
    
    try:
        demo_position_awareness()
    except Exception as e:
        print(f"Position Awareness Error: {e}")
    
    try:
        demo_persistence()
    except Exception as e:
        print(f"Persistence Error: {e}")
    
    print_separator("DEMO COMPLETED")
    print("\nTo run the full GUI:")
    print("  python start_v1.py")
    print("\nTo run with LLM:")
    print("  python start_v1.py --llm")


if __name__ == "__main__":
    run_all_demos()
