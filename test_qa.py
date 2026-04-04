#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test Q&A functionality"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from blueclaw import create_coordinator_v3

async def test_qa():
    """Test question answering"""
    
    test_cases = [
        ("你好", "greeting"),
        ("你是谁", "identity"),
        ("你能做什么", "capabilities"),
        ("hello", "greeting"),
        ("what can you do", "capabilities"),
    ]
    
    for text, expected_type in test_cases:
        print(f"\n[Test] Input: '{text}'")
        print("-" * 50)
        
        coord = create_coordinator_v3(use_real_execution=False)
        
        captured = {}
        
        def on_message(msg):
            if '[THINK]' not in msg and '[INIT]' not in msg and '[TASK]' not in msg:
                captured['response'] = msg
        
        coord.set_callbacks(on_message=on_message)
        
        await coord.start_task(text)
        
        if 'response' in captured:
            response = captured['response']
            # Check if it's not the default template
            if "请告诉我具体你想做什么" in response or "general_task" in response:
                print(f"[FAIL] Got default template response")
            else:
                print(f"[PASS] Got proper response:")
                print(f"  {response[:100]}...")
        else:
            print(f"[FAIL] No response captured")

if __name__ == "__main__":
    asyncio.run(test_qa())
