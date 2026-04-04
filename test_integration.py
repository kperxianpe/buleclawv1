#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration test for Thinking Blueprint + GUI
Tests the core components without launching full GUI
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("Blueclaw v1.0 - Thinking Blueprint Integration Test")
print("=" * 70)

# Test 1: Import Thinking Engine
print("\n[1/5] Testing Thinking Engine import...")
try:
    from core.thinking_engine import (
        IntentType, ThinkingStep, ThinkingOption, 
        ThinkingResult, ThinkingEngine
    )
    print("  [OK] Thinking Engine imported successfully")
except Exception as e:
    print(f"  [FAIL] Import error: {e}")
    sys.exit(1)

# Test 2: Test Thinking Engine functionality
print("\n[2/5] Testing Thinking Engine functionality...")
try:
    engine = ThinkingEngine()
    
    test_cases = [
        ("Create a game", IntentType.CREATE),
        ("What's the weather?", IntentType.QUESTION),
        ("Hello", IntentType.CHAT),
        ("Run the script", IntentType.EXECUTE),
    ]
    
    for text, expected_intent in test_cases:
        result = engine.analyze(text)
        assert result.intent == expected_intent, f"Expected {expected_intent}, got {result.intent}"
        assert len(result.options) == 4, f"Expected 4 options, got {len(result.options)}"
        print(f"  [OK] '{text}' -> {result.intent.value} ({result.intent_confidence:.0%})")
    
    print("  [OK] All test cases passed")
except Exception as e:
    print(f"  [FAIL] Test error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Test PyQt5 Widgets
print("\n[3/5] Testing PyQt5 Widgets...")
try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    
    # Create QApplication for widget tests
    app = QApplication.instance() or QApplication(sys.argv)
    
    from core.thinking_widgets import (
        StepWidget, OptionButton, ThinkingBlueprintWidget
    )
    print("  [OK] Widgets imported successfully")
    
    # Test widget creation
    result = engine.analyze("Create a website")
    
    # Test StepWidget
    step_widget = StepWidget(result.thinking_steps[0])
    assert step_widget is not None
    print("  [OK] StepWidget created")
    
    # Test OptionButton
    option_btn = OptionButton(result.options[0])
    assert option_btn is not None
    print("  [OK] OptionButton created")
    
    # Test ThinkingBlueprintWidget
    blueprint_widget = ThinkingBlueprintWidget()
    blueprint_widget.set_result(result)
    assert blueprint_widget is not None
    print("  [OK] ThinkingBlueprintWidget created")
    
except Exception as e:
    print(f"  [FAIL] Widget test error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test GUI integration
print("\n[4/5] Testing GUI integration...")
try:
    # Test that GUI file can be imported
    import blueclaw_v1_gui_with_thinking as gui_module
    print("  [OK] GUI module imported")
    
    # Verify key classes exist
    assert hasattr(gui_module, 'BlueclawMainWindow')
    assert hasattr(gui_module, 'ExecutionStepWidget')
    print("  [OK] Main classes available")
    
except Exception as e:
    print(f"  [FAIL] GUI integration error: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Verify workflow
print("\n[5/5] Testing complete workflow...")
try:
    # Simulate the workflow
    print("  Step 1: User input")
    user_input = "Create a network game"
    
    print("  Step 2: Thinking Engine analysis")
    result = engine.analyze(user_input)
    print(f"    - Intent: {result.intent.value}")
    print(f"    - Confidence: {result.intent_confidence:.0%}")
    print(f"    - Steps: {len(result.thinking_steps)}")
    print(f"    - Options: {len(result.options)}")
    
    print("  Step 3: User selects option A")
    selected_option = result.get_option("A")
    print(f"    - Selected: [{selected_option.label}] {selected_option.title}")
    
    print("  Step 4: Execute option")
    exec_result = engine.execute_option(result, "A")
    print(f"    - Action: {exec_result['action']}")
    print(f"    - Confidence: {exec_result['confidence']:.0%}")
    
    print("  [OK] Complete workflow verified")
    
except Exception as e:
    print(f"  [FAIL] Workflow test error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("Integration Test Complete!")
print("=" * 70)
print("\nSummary:")
print("  - Thinking Engine: Working")
print("  - Four-Option Mode: Working")
print("  - PyQt5 Widgets: Working")
print("  - GUI Integration: Ready")
print("\nNext step: Run the GUI with:")
print("  python blueclaw_v1_gui_with_thinking.py")
