#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Thinking Blueprint 引擎
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from blueclaw.core.thinking_options import ThinkingBlueprintEngine


def test_thinking():
    """Test thinking engine"""
    print("=" * 60)
    print("Blueclaw v1.0 - Thinking Blueprint Test")
    print("=" * 60)
    print("")
    
    engine = ThinkingBlueprintEngine()
    
    test_inputs = [
        "帮我创建一个网络多人游戏",
        "你好",
        "帮我整理桌面文件",
        "解释一下量子计算",
        "运行测试",
    ]
    
    for user_input in test_inputs:
        print(f"\n{'='*60}")
        print(f"User: {user_input}")
        print(f"{'='*60}")
        
        # Analyze
        result = engine.analyze(user_input)
        
        # Show intent
        print(f"\n[Intent Recognition]")
        print(f"  Intent: {result.intent.value.upper()}")
        print(f"  Confidence: {result.intent_confidence:.0%}")
        
        # Show thinking
        print(f"\n[Thinking Process]")
        for step in result.thinking_steps:
            print(f"  Step {step.step_number}: {step.title}")
            print(f"     {step.content}")
        
        # Show options
        print(f"\n[4-Option UI]")
        print("-" * 50)
        for opt in result.options:
            bar = "#" * int(opt.confidence / 10) + "-" * (10 - int(opt.confidence / 10))
            print(f"\n  [{opt.option_id}] {opt.title}")
            print(f"      {opt.description}")
            print(f"      Match: {bar} {opt.confidence}%")
        
        # Simulate selection
        if result.options:
            selected = result.options[0]
            exec_result = engine.execute_option(result, selected.option_id)
            print(f"\n[Execute] Selected {selected.option_id}: {exec_result['action']}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    test_thinking()
