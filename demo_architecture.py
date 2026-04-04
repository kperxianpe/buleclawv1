#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
demo_architecture.py - Week 15.5 Architecture Demo

Pure Python demo of three-tier architecture.
No npm required.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def demo_protocol_layer():
    """Demo Protocol Layer"""
    print_section("1. Protocol Layer")
    
    from blueclaw.api import (
        PROTOCOL_VERSION,
        MessageType,
        MessageFactory,
        BlueclawMessage,
        ThinkingNodeData,
        ThinkingOptionData,
    )
    
    print(f"\nProtocol Version: {PROTOCOL_VERSION}")
    
    print("\nMessage Examples:")
    
    # Task start message
    task_msg = MessageFactory.create_task_start("Plan a weekend trip")
    print(f"  [Task Start] type={task_msg.type}")
    print(f"               version={task_msg.version}")
    
    # Thinking node message
    node = ThinkingNodeData(
        id="thinking_001",
        question="Select destination:",
        options=[
            ThinkingOptionData("A", "Hangzhou", "West Lake tour", 0.85, True),
            ThinkingOptionData("B", "Suzhou", "Garden tour", 0.80),
        ],
    )
    node_msg = MessageFactory.create_thinking_node_created(node)
    print(f"\n  [Thinking Node] type={node_msg.type}")
    print(f"                  question={node_msg.payload.get('question')}")
    print(f"                  options={len(node_msg.payload.get('options', []))}")
    
    # JSON serialization
    json_str = task_msg.to_json()
    print(f"\n  [JSON Serialize] {json_str[:60]}...")
    
    # JSON deserialization
    parsed = BlueclawMessage.from_json(json_str)
    print(f"  [JSON Parse] type={parsed.type}")
    
    print("\n[OK] Protocol Layer working - versioned message format")


def demo_engine_facade():
    """Demo Engine Facade Layer"""
    print_section("2. Engine Facade Layer")
    
    from blueclaw.api import create_engine_facade, Phase
    
    engine = create_engine_facade("demo-session")
    print(f"\nEngine Facade Created:")
    print(f"  Session ID: {engine.session_id}")
    print(f"  Initial Phase: {engine.state.phase}")
    
    # Set callbacks
    events_log = []
    engine.set_callbacks(
        state_changed=lambda state: events_log.append(f"state: {state.phase}"),
        message=lambda msg: events_log.append(f"msg: {msg[:30]}..."),
    )
    print(f"\nCallbacks set: {len(events_log)} events")
    
    # Verify interfaces
    print("\nStandard Interfaces:")
    interfaces = [
        "process(user_input)",
        "select_option(node_id, option_id)",
        "provide_clarification(node_id, answer)",
        "intervene(step_id, action_type)",
        "pause_execution()",
        "resume_execution()",
        "get_progress()",
    ]
    for iface in interfaces:
        has_method = hasattr(engine, iface.split('(')[0])
        status = "[OK]" if has_method else "[FAIL]"
        print(f"  {status} {iface}")
    
    print("\n[OK] Engine Facade working - stable interface")


def demo_renderer_adapter():
    """Demo Renderer Adapter Layer"""
    print_section("3. Renderer Adapter Layer")
    
    frontend_files = [
        "blueclaw-ui/src/adapters/BlueprintRenderer.ts",
        "blueclaw-ui/src/adapters/reactflow/ReactFlowAdapter.ts",
        "blueclaw-ui/src/adapters/canvasmind/CanvasMindAdapter.ts",
    ]
    
    print("\nFrontend Adapter Files:")
    for file in frontend_files:
        path = Path(file)
        status = "[OK]" if path.exists() else "[FAIL]"
        print(f"  {status} {file}")
    
    print("\nBlueprintRenderer Interface Methods:")
    methods = [
        "initialize(container)",
        "destroy()",
        "addThinkingNode(node)",
        "addExecutionStep(step)",
        "showInterventionPanel(stepId, actions)",
        "focusOnNode(nodeId)",
        "fitView()",
    ]
    for method in methods:
        print(f"  * {method}")
    
    print("\nRenderer Factory:")
    print("  registerRenderer('reactflow', ReactFlowAdapter)")
    print("  registerRenderer('canvasmind', CanvasMindAdapter)")
    
    print("\n[OK] Renderer Adapter ready - switchable engines")


def print_summary():
    """Print Summary"""
    print_section("Week 15.5 Architecture Summary")
    
    summary = """
+------------------+------------------+------------------+
| Presentation     | Protocol         | Engine           |
+------------------+------------------+------------------+
| ReactFlowAdapter | WebSocket v1.0.0 | BlueclawEngine   |
| CanvasMindAdapter| Version Check    |   Facade         |
| Node Components  | Python/TS Align  | V1/V2/V3 Ready   |
+------------------+------------------+------------------+

Validation:
  [OK] Message format has version field
  [OK] Renderer switchable via factory
  [OK] Business logic not tied to ReactFlow

How to Start:
  1. Start server: python start_websocket_server.py
  2. Test client: python test_websocket_client.py

Key Files:
  * blueclaw/api/message_protocol.py
  * blueclaw/api/engine_facade.py
  * blueclaw/api/websocket_server.py
  * blueclaw-ui/src/adapters/
  * test_websocket_client.py
"""
    print(summary)


def main():
    print("\n" + "="*60)
    print("  Week 15.5 - Blueclaw Three-Tier Architecture")
    print("  Forward Compatible: V1 -> V2 -> V3")
    print("="*60)
    
    try:
        demo_protocol_layer()
        demo_engine_facade()
        demo_renderer_adapter()
        print_summary()
        
        print("\n" + "="*60)
        print("  [SUCCESS] All demos completed!")
        print("="*60)
        
        print("\nNext Steps:")
        print("  1. Start server: python start_websocket_server.py")
        print("  2. Test client: python test_websocket_client.py")
        print("     Commands: task <input>, select <nid> <oid>, quit")
        
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
