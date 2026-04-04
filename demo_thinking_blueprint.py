#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script for Blueclaw v1.0 Thinking Blueprint
演示思考蓝图功能（无需启动完整GUI）
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.thinking_engine import ThinkingEngine, IntentType


def print_separator(char="=", length=70):
    print(char * length)


def demo_thinking_blueprint():
    """Demonstrate Thinking Blueprint functionality"""
    
    engine = ThinkingEngine()
    
    test_cases = [
        ("Create a multiplayer game", "CREATE mode"),
        ("What's the weather today?", "QUESTION mode"),
        ("Hello, how are you?", "CHAT mode"),
        ("Run the analysis script", "EXECUTE mode"),
        ("Fix the bug in my code", "MODIFY mode"),
        ("Check system status", "ANALYZE mode"),
        ("Organize my desktop files", "UNKNOWN mode"),
    ]
    
    print_separator()
    print("Blueclaw v1.0 - Thinking Blueprint Demo")
    print("四选项交互模式演示")
    print_separator()
    
    for user_input, description in test_cases:
        print(f"\n{'='*70}")
        print(f"USER INPUT: \"{user_input}\"")
        print(f"Mode: {description}")
        print(f"{'='*70}\n")
        
        # Analyze input
        result = engine.analyze(user_input)
        
        # Show intent
        print("[INTENT RECOGNITION]")
        print(f"  Intent: {result.intent.value.upper()}")
        print(f"  Confidence: {result.intent_confidence:.0%}")
        print()
        
        # Show thinking steps
        print("[THINKING PROCESS]")
        for step in result.thinking_steps:
            print(f"  Step {step.step_number}: {step.icon} {step.title}")
            print(f"    {step.description}")
        print()
        
        # Show 4 options
        print("[4-OPTION MODE]")
        print("-" * 50)
        
        for opt in result.options:
            # Confidence bar (using ASCII characters)
            bar_length = 10
            filled = int(opt.confidence / 100 * bar_length)
            bar = "#" * filled + "-" * (bar_length - filled)
            
            print(f"\n  [{opt.label}] {opt.icon} {opt.title}")
            print(f"      {opt.description}")
            print(f"      Match: {bar} {opt.confidence}%")
        
        # Simulate user selection
        if result.options:
            selected = result.options[0]
            exec_result = engine.execute_option(result, selected.option_id)
            print(f"\n  [EXECUTION]")
            print(f"    Selected: [{selected.option_id}] {selected.title}")
            print(f"    Action: {exec_result['action']}")
            print(f"    Confidence: {exec_result['confidence']:.0%}")
    
    print("\n" + "=" * 70)
    print("Demo completed!")
    print("=" * 70)
    print("\nKey Features:")
    print("  [+] Intent Recognition - 7 intent types with confidence scores")
    print("  [+] Thinking Process - Visual step-by-step analysis")
    print("  [+] 4-Option Mode - Context-aware action options")
    print("  [+] Confidence Bars - Visual confidence indicators")
    print("\nTo launch the full GUI:")
    print("  python start_blueclaw_v1.py")


if __name__ == "__main__":
    try:
        demo_thinking_blueprint()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
