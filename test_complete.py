#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_complete.py - Complete Architecture Test

Tests all three layers without requiring external connections.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


def test_all_layers():
    print("="*60)
    print("Week 15.5 - Complete Architecture Test")
    print("="*60)
    
    # Test 1: Protocol Layer
    print("\n[1] Testing Protocol Layer...")
    from blueclaw.api import (
        PROTOCOL_VERSION, MessageType, MessageFactory, 
        BlueclawMessage, ThinkingNodeData, ThinkingOptionData
    )
    
    assert PROTOCOL_VERSION == "1.0.0"
    msg = MessageFactory.create_task_start("test")
    assert msg.version == PROTOCOL_VERSION
    assert "version" in msg.to_dict()
    print("    [OK] Protocol version 1.0.0")
    print("    [OK] Message serialization works")
    
    # Test 2: Engine Facade
    print("\n[2] Testing Engine Facade Layer...")
    from blueclaw.api import create_engine_facade
    
    engine = create_engine_facade("test")
    assert hasattr(engine, 'process')
    assert hasattr(engine, 'select_option')
    assert hasattr(engine, 'intervene')
    print("    [OK] Engine facade created")
    print("    [OK] All interface methods present")
    
    # Test 3: Renderer Adapter
    print("\n[3] Testing Renderer Adapter Layer...")
    from blueclaw.api import BlueclawEngineFacade
    
    # Check frontend files exist
    files = [
        "blueclaw-ui/src/adapters/BlueprintRenderer.ts",
        "blueclaw-ui/src/adapters/reactflow/ReactFlowAdapter.ts",
        "blueclaw-ui/src/adapters/canvasmind/CanvasMindAdapter.ts",
    ]
    for f in files:
        assert Path(f).exists(), f"Missing: {f}"
    print("    [OK] Frontend adapter files present")
    print("    [OK] ReactFlow and CanvasMind adapters defined")
    
    # Test 4: Data Flow
    print("\n[4] Testing Data Flow...")
    node = ThinkingNodeData(
        id="node_1",
        question="Test question?",
        options=[ThinkingOptionData("A", "Option A", "Desc", 0.8)]
    )
    msg = MessageFactory.create_thinking_node_created(node)
    assert msg.type == MessageType.THINKING_NODE_CREATED
    print("    [OK] Thinking node message created")
    
    step_data = {
        "id": "step_1",
        "name": "Test Step",
        "description": "A test step",
        "dependencies": []
    }
    from blueclaw.api import ExecutionStepData
    step = ExecutionStepData(**step_data)
    print("    [OK] Execution step data created")
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60)
    print("""
Architecture Summary:
+------------------+------------------+------------------+
| Presentation     | Protocol         | Engine           |
+------------------+------------------+------------------+
| ReactFlowAdapter | WebSocket v1.0.0 | BlueclawEngine   |
| CanvasMindAdapter| Version Check    |   Facade         |
| Node Components  | Python/TS Align  | V1/V2/V3 Ready   |
+------------------+------------------+------------------+

To run the full system:
1. Terminal 1: python start_websocket_server.py
2. Terminal 2: python test_websocket_client.py
    """)
    return True


if __name__ == "__main__":
    try:
        test_all_layers()
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
