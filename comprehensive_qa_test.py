#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
comprehensive_qa_test.py - Command-line Q&A Comprehensive Test
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from blueclaw import create_coordinator_v3

# Test cases: (input, expected_behavior, category)
TEST_CASES = [
    # ============ Greetings ============
    ("你好", "Greeting", "greeting"),
    ("Hello", "Greeting in English", "greeting"),
    ("Hi", "Short greeting", "greeting"),
    ("hey", "Casual greeting", "greeting"),
    ("在吗", "Presence check", "greeting"),
    ("早上好", "Time-based greeting", "greeting"),
    
    # ============ Identity Questions ============
    ("你是谁", "Identity introduction", "identity"),
    ("你是什么", "What is it", "identity"),
    ("who are you", "Identity in English", "identity"),
    ("what are you", "What are you", "identity"),
    ("介绍一下你自己", "Self introduction", "identity"),
    
    # ============ Capability Questions ============
    ("你能做什么", "List capabilities", "capability"),
    ("你会什么", "What can you do", "capability"),
    ("what can you do", "Capabilities in English", "capability"),
    ("help", "Help command", "capability"),
    ("有什么功能", "Feature list", "capability"),
    
    # ============ Task - File Operations ============
    ("列出当前目录的文件", "List files", "task_file"),
    ("显示当前文件夹内容", "Show folder contents", "task_file"),
    ("获取目录列表", "Get directory list", "task_file"),
    ("查看文件", "View files", "task_file"),
    ("列出所有txt文件", "List txt files", "task_file"),
    
    # ============ Task - Travel Planning ============
    ("我想规划周末旅行", "Travel planning", "task_travel"),
    ("规划去杭州的旅行", "Hangzhou travel", "task_travel"),
    ("推荐短途旅游目的地", "Suggest destinations", "task_travel"),
    ("周末去哪里玩", "Weekend trip ideas", "task_travel"),
    ("旅游推荐", "Travel recommendations", "task_travel"),
    
    # ============ Task - Code Generation ============
    ("写一个Python脚本", "Generate Python script", "task_code"),
    ("批量重命名图片文件", "Rename images", "task_code"),
    ("写计算斐波那契的函数", "Fibonacci function", "task_code"),
    ("写一个排序算法", "Sorting algorithm", "task_code"),
    ("写爬虫代码", "Web scraper", "task_code"),
    
    # ============ Task - Data Analysis ============
    ("分析这个CSV文件", "Analyze CSV", "task_data"),
    ("数据统计", "Data statistics", "task_data"),
    ("生成图表", "Generate charts", "task_data"),
    
    # ============ Edge Cases ============
    ("???", "Unknown input", "edge"),
    ("123456", "Numeric input", "edge"),
    ("test", "Simple text", "edge"),
    (".......", "Punctuation only", "edge"),
    ("怎么做", "How to do", "edge"),
]


class QATestRunner:
    """Test runner"""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
    
    def log(self, message: str, level: str = "INFO"):
        """Log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    async def run_test(self, test_input: str, expected: str, category: str) -> dict:
        """Run single test"""
        self.log(f"Testing: '{test_input}'")
        self.log(f"  Expected: {expected}")
        
        coord = create_coordinator_v3(use_real_execution=False)
        
        # Capture callbacks
        captured = {
            'result_type': None,
            'response': None,
            'options': None,
            'preview': None
        }
        
        def on_execution_preview(preview):
            captured['result_type'] = 'execution_preview'
            captured['preview'] = preview
        
        def on_question(question):
            captured['result_type'] = 'question'
            captured['response'] = question.text
        
        def on_options(options):
            captured['result_type'] = 'options'
            captured['options'] = options
        
        def on_message(msg):
            if 'AI:' in msg and not captured['response']:
                captured['response'] = msg.replace('AI:', '').strip()
        
        coord.set_callbacks(
            on_execution_preview=on_execution_preview,
            on_question=on_question,
            on_options=on_options,
            on_message=on_message
        )
        
        # Run test
        try:
            await coord.start_task(test_input)
            
            state = coord.state.phase
            result_type = captured['result_type']
            
            # Determine success based on category
            success = False
            reason = ""
            
            if category == "greeting":
                success = state == "completed" and captured['response'] is not None
                reason = "Should respond with greeting"
                
            elif category == "identity":
                success = state == "completed" and captured['response'] is not None
                reason = "Should introduce itself"
                
            elif category == "capability":
                success = state == "completed" and captured['response'] is not None
                reason = "Should list capabilities"
                
            elif category in ["task_file", "task_travel", "task_code", "task_data"]:
                success = result_type in ['execution_preview', 'options']
                reason = "Should generate execution blueprint or options"
                
            elif category == "edge":
                success = True  # Edge cases should not crash
                reason = "Should handle gracefully"
            
            result = {
                'input': test_input,
                'expected': expected,
                'category': category,
                'state': state,
                'result_type': result_type,
                'success': success,
                'reason': reason,
                'response': captured['response']
            }
            
            if success:
                self.log(f"  [PASS] {reason}", "PASS")
                self.passed += 1
            else:
                self.log(f"  [FAIL] {reason}", "FAIL")
                self.log(f"    State: {state}, Type: {result_type}", "DEBUG")
                self.failed += 1
            
            return result
            
        except Exception as e:
            self.log(f"  [ERROR] {e}", "ERROR")
            self.failed += 1
            return {
                'input': test_input,
                'expected': expected,
                'category': category,
                'success': False,
                'error': str(e)
            }
    
    async def run_all_tests(self):
        """Run all tests"""
        self.log("="*70, "HEADER")
        self.log("Blueclaw v1.0 - Comprehensive Q&A Test Suite", "HEADER")
        self.log("="*70, "HEADER")
        self.log(f"Total test cases: {len(TEST_CASES)}")
        self.log("")
        
        # Group by category
        categories = {}
        for inp, exp, cat in TEST_CASES:
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((inp, exp))
        
        # Run tests by category
        all_results = []
        for category, tests in categories.items():
            self.log(f"\n{'='*70}", "CATEGORY")
            self.log(f"Category: {category.upper()} ({len(tests)} tests)", "CATEGORY")
            self.log("="*70, "CATEGORY")
            
            for test_input, expected in tests:
                result = await self.run_test(test_input, expected, category)
                all_results.append(result)
                await asyncio.sleep(0.1)  # Brief pause
        
        # Summary
        self.print_summary(all_results)
    
    def print_summary(self, results):
        """Print test summary"""
        self.log("\n" + "="*70, "SUMMARY")
        self.log("TEST SUMMARY", "SUMMARY")
        self.log("="*70, "SUMMARY")
        
        total = len(results)
        passed = sum(1 for r in results if r.get('success'))
        failed = total - passed
        
        self.log(f"Total: {total}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {failed}")
        self.log(f"Success Rate: {passed/total*100:.1f}%")
        
        if failed > 0:
            self.log("\nFailed Tests:", "FAIL")
            for r in results:
                if not r.get('success'):
                    self.log(f"  - {r['input']}: {r.get('reason', 'Unknown')}", "FAIL")
        
        # Category breakdown
        self.log("\nCategory Breakdown:", "INFO")
        categories = {}
        for r in results:
            cat = r['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'passed': 0}
            categories[cat]['total'] += 1
            if r.get('success'):
                categories[cat]['passed'] += 1
        
        for cat, stats in sorted(categories.items()):
            rate = stats['passed']/stats['total']*100
            status = "OK" if rate == 100 else "PARTIAL" if rate > 50 else "FAIL"
            self.log(f"  {cat}: {stats['passed']}/{stats['total']} ({rate:.0f}%) [{status}]")
        
        self.log("="*70, "SUMMARY")


async def main():
    """Main entry"""
    runner = QATestRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
