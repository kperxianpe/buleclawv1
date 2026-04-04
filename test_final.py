#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Final test for Q&A and Task execution"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from blueclaw import create_coordinator_v3

async def test():
    print("=" * 60)
    print("Final Verification Test")
    print("=" * 60)
    
    # Test 1: Q&A
    print("\n[Test 1] Q&A: '你好'")
    coord = create_coordinator_v3(use_real_execution=False)
    await coord.start_task('你好')
    print(f"  State: {coord.state.phase}")
    assert coord.state.phase == "completed", "Should complete Q&A immediately"
    print("  [PASS]")
    
    # Test 2: Task execution
    print("\n[Test 2] Task: '列出当前目录的文件'")
    coord2 = create_coordinator_v3(use_real_execution=True)
    
    blueprint_loaded = []
    def on_bp(steps):
        blueprint_loaded.append(len(steps))
        print(f"  Blueprint: {len(steps)} steps")
    
    coord2.set_callbacks(on_blueprint_loaded=on_bp)
    await coord2.start_task('列出当前目录的文件')
    print(f"  State: {coord2.state.phase}")
    assert len(blueprint_loaded) > 0, "Should load blueprint"
    print("  [PASS]")
    
    # Test 3: Identity question
    print("\n[Test 3] Q&A: '你是谁'")
    coord3 = create_coordinator_v3(use_real_execution=False)
    await coord3.start_task('你是谁')
    print(f"  State: {coord3.state.phase}")
    assert coord3.state.phase == "completed", "Should complete Q&A immediately"
    print("  [PASS]")
    
    print("\n" + "=" * 60)
    print("All tests PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test())
