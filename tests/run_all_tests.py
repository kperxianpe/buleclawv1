#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all_tests.py - Run all test suites

Executes:
1. Unit tests
2. Integration tests
3. GUI tests
4. Stress tests
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


def run_test_file(test_file: str, description: str) -> bool:
    """运行单个测试文件"""
    print("\n" + "="*70)
    print(f"Running: {description}")
    print("="*70)
    
    test_path = Path(__file__).parent / test_file
    
    if not test_path.exists():
        print(f"[SKIP] Test file not found: {test_file}")
        return True
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] Test took too long: {test_file}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to run test: {e}")
        return False


def main():
    """主函数"""
    print("="*70)
    print("Blueclaw v1.0 - Complete Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    tests = [
        ("test_gui_unit.py", "GUI Unit Tests"),
        ("test_integration.py", "Core Integration Tests"),
        ("test_gui_integration.py", "GUI Integration Tests"),
        ("../comprehensive_qa_test.py", "Comprehensive Q&A Tests"),
    ]
    
    results = []
    
    for test_file, description in tests:
        success = run_test_file(test_file, description)
        results.append((description, success))
    
    # Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for _, s in results if s)
    
    for desc, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {desc}")
    
    print("-"*70)
    print(f"Total: {total}, Passed: {passed}, Failed: {total - passed}")
    print("="*70)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
