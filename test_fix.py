#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the fixes for the execution bug"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from blueclaw import create_coordinator_v3

async def test_file_list():
    """Test: '列出当前目录的文件' should execute"""
    print("Test: '列出当前目录的文件'")
    print("=" * 60)
    
    coord = create_coordinator_v3(use_real_execution=True)
    
    captured = {}
    
    def on_execution_preview(preview):
        captured['preview'] = preview
        print(f"[Execution Preview Generated]")
        print(f"  Task type: {preview.task_type}")
        print(f"  Steps ({len(preview.steps)}):")
        for i, step in enumerate(preview.steps):
            print(f"    {i+1}. {step.get('name', 'Unnamed')}")
    
    def on_blueprint_loaded(steps):
        captured['blueprint'] = steps
        print(f"[Blueprint Loaded] {len(steps)} steps")
        for i, step in enumerate(steps):
            print(f"  {i+1}. {step.name}")
    
    def on_step_update(step_id, status, index):
        print(f"[Step Update] {step_id}: {status}")
    
    def on_execution_complete(result):
        captured['result'] = result
        print(f"[Execution Complete] {result.get('summary')}")
    
    coord.set_callbacks(
        on_execution_preview=on_execution_preview,
        on_blueprint_loaded=on_blueprint_loaded,
        on_step_update=on_step_update,
        on_execution_complete=on_execution_complete
    )
    
    # Start task
    await coord.start_task('列出当前目录的文件')
    
    # Check result
    if 'preview' in captured or 'blueprint' in captured:
        print("\n[PASS] Execution blueprint generated successfully!")
    elif 'result' in captured:
        print("\n[PASS] Task executed successfully!")
    else:
        print("\n[FAIL] No execution - check the logic")
        print(f"Current state: {coord.state.phase}")


async def test_greeting():
    """Test: Greeting should get proper response"""
    print("\n\nTest: '你好'")
    print("=" * 60)
    
    coord = create_coordinator_v3(use_real_execution=False)
    
    captured = {}
    
    def on_message(msg):
        if '[THINK]' not in msg and '[INIT]' not in msg:
            captured['response'] = msg
            print(f"AI Response: {msg}")
    
    coord.set_callbacks(on_message=on_message)
    
    await coord.start_task('你好')
    
    if 'response' in captured:
        print("\n[PASS] Got response")
    else:
        print("\n[FAIL] No response")


async def main():
    await test_file_list()
    await test_greeting()


if __name__ == "__main__":
    asyncio.run(main())
