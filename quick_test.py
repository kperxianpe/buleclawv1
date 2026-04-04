#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from blueclaw import create_coordinator_v3

async def test_travel_options():
    """Test: Travel planning should provide options"""
    print("Testing: Travel planning - should provide options")
    print("=" * 60)
    
    coord = create_coordinator_v3(use_real_execution=False)
    
    captured = {}
    
    def on_options(options):
        captured['options'] = options
        print(f"Options provided:")
        for opt in options:
            print(f"  [{opt.id}] {opt.label}")
    
    def on_question(question):
        captured['question'] = question
        print(f"Question: {question.text}")
        if question.options:
            for opt in question.options:
                print(f"  [{opt['id']}] {opt['label']}")
    
    coord.set_callbacks(on_question=on_question, on_options=on_options)
    
    # Test 1: Vague input
    print("\n[Test 1] Input: '规划周末旅行'")
    await coord.start_task('规划周末旅行')
    
    if 'options' in captured:
        print(f"[PASS] System provided {len(captured['options'])} options")
    elif 'question' in captured:
        print(f"[QUESTION] {captured['question'].text}")
        # Check if it's asking directly about destination
        if '哪里' in captured['question'].text or 'where' in captured['question'].text.lower():
            print("[FAIL] System is asking directly about destination")
        else:
            print("[PASS] System is providing guided options")
    else:
        print("[NO RESPONSE]")
    
    # Test 2: File rename scenario
    print("\n" + "=" * 60)
    print("\n[Test 2] Input: '批量重命名图片文件'")
    
    captured.clear()
    await coord.start_task('批量重命名图片文件')
    
    if 'options' in captured:
        print(f"[PASS] System provided {len(captured['options'])} options")
    elif 'question' in captured:
        print(f"[QUESTION] {captured['question'].text}")
    else:
        print("[NO RESPONSE]")
    
    print("\n" + "=" * 60)
    print("Test completed")

if __name__ == "__main__":
    asyncio.run(test_travel_options())
