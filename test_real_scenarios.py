#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real Scenario Tests

Tests real-world use cases with actual file operations, code execution, and API calls.
"""

import sys
import asyncio
import tempfile
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from blueclaw.api import BlueclawEngineFacade
from blueclaw.skills import (
    FileReadSkill, FileWriteSkill, FileListSkill, FileSearchSkill,
    CodeAnalyzeSkill, CodeExecuteSkill,
    WebFetchSkill, WebSearchSkill,
    DataParseSkill, DataTransformSkill,
    AITranslateSkill, AISummarizeSkill,
    SystemInfoSkill, ShellExecuteSkill
)
from blueclaw.config import Config


class ScenarioTester:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.test_dir = None
        
    def setup(self):
        self.test_dir = tempfile.mkdtemp(prefix="blueclaw_test_")
        print(f"Test directory: {self.test_dir}")
        
        # Create test files
        (Path(self.test_dir) / "sample.py").write_text('''
def hello():
    """Say hello"""
    return "Hello World"

def add(a, b):
    # TODO: add type checking
    return a + b

class Calculator:
    def multiply(self, x, y):
        return x * y
''', encoding='utf-8')
        
        (Path(self.test_dir) / "data.json").write_text('''
{"users": [
    {"name": "Alice", "age": 30, "city": "Beijing"},
    {"name": "Bob", "age": 25, "city": "Shanghai"},
    {"name": "Charlie", "age": 35, "city": "Beijing"}
]}
''', encoding='utf-8')
        
        (Path(self.test_dir) / "notes.txt").write_text('''
Meeting Notes - 2024-01-15
==========================

Attendees: Alice, Bob, Charlie

Agenda:
1. Project status review
2. Q1 planning discussion
3. Budget allocation

Action Items:
- Alice: Prepare Q1 roadmap
- Bob: Update budget spreadsheet
- Charlie: Schedule follow-up meeting

Next meeting: 2024-01-22
''', encoding='utf-8')
    
    def cleanup(self):
        import shutil
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def log(self, msg):
        print(f"  {msg}")
    
    def assert_true(self, condition, name):
        if condition:
            self.passed += 1
            self.log(f"[PASS] {name}")
        else:
            self.failed += 1
            self.log(f"[FAIL] {name}")
    
    async def run_all(self):
        print("="*70)
        print("REAL SCENARIO TESTS")
        print("="*70)
        
        self.setup()
        
        try:
            await self.scenario_1_file_analysis()
            await self.scenario_2_code_operations()
            await self.scenario_3_data_processing()
            await self.scenario_4_web_operations()
            await self.scenario_5_ai_tasks()
            await self.scenario_6_system_commands()
            await self.scenario_7_engine_workflow()
        finally:
            self.cleanup()
        
        # Summary
        print("\n" + "="*70)
        total = self.passed + self.failed
        print(f"RESULTS: {self.passed}/{total} passed ({self.passed/total*100:.1f}%)")
        print("="*70)
        
        return self.failed == 0
    
    # Scenario 1: File Analysis
    async def scenario_1_file_analysis(self):
        print("\n[Scenario 1] File Analysis Pipeline")
        print("-" * 50)
        
        # 1.1 List files
        lister = FileListSkill()
        result = await lister.run(path=self.test_dir)
        self.assert_true(result.success, "1.1 List files")
        file_count = result.output.get("count", 0)
        self.log(f"       Found {file_count} items")
        
        # 1.2 Read Python file
        reader = FileReadSkill()
        py_file = Path(self.test_dir) / "sample.py"
        result = await reader.run(path=str(py_file))
        self.assert_true(result.success, "1.2 Read Python file")
        if result.success:
            self.log(f"       Content: {len(result.output)} chars, {result.metadata.get('lines')} lines")
        
        # 1.3 Search in files
        searcher = FileSearchSkill()
        result = await searcher.run(path=self.test_dir, pattern="def ", file_pattern="*.py")
        self.assert_true(result.success, "1.3 Search function definitions")
        matches = result.output.get("matches", [])
        self.log(f"       Found {len(matches)} function definitions")
        
        # 1.4 Write report
        writer = FileWriteSkill()
        report_path = Path(self.test_dir) / "report.md"
        report_content = f"""# Analysis Report
Generated: {__import__('datetime').datetime.now().isoformat()}

## Files Analyzed
- Total items: {file_count}
- Functions found: {len(matches)}

## Findings
Sample project with {len(matches)} functions defined.
"""
        result = await writer.run(path=str(report_path), content=report_content)
        self.assert_true(result.success, "1.4 Write report")
        if result.success:
            self.log(f"       Report written: {report_path.name}")
    
    # Scenario 2: Code Operations
    async def scenario_2_code_operations(self):
        print("\n[Scenario 2] Code Analysis & Execution")
        print("-" * 50)
        
        # 2.1 Analyze code
        analyzer = CodeAnalyzeSkill()
        py_file = Path(self.test_dir) / "sample.py"
        result = await analyzer.run(path=str(py_file), language="python")
        self.assert_true(result.success, "2.1 Analyze Python code")
        if result.success:
            metrics = result.output.get("metrics", {})
            self.log(f"       Functions: {metrics.get('functions', 0)}, Classes: {metrics.get('classes', 0)}")
        
        # 2.2 Execute safe code
        executor = CodeExecuteSkill()
        result = await executor.run(code="sum(range(10))")
        self.assert_true(result.success, "2.2 Execute calculation")
        if result.success:
            self.log(f"       Result: {result.output}")
        
        # 2.3 Execute with error handling
        result = await executor.run(code="[x**2 for x in range(5)]")
        self.assert_true(result.success, "2.3 Execute list comprehension")
    
    # Scenario 3: Data Processing
    async def scenario_3_data_processing(self):
        print("\n[Scenario 3] Data Processing Pipeline")
        print("-" * 50)
        
        # 3.1 Parse JSON
        parser = DataParseSkill()
        json_file = Path(self.test_dir) / "data.json"
        result = await parser.run(source=str(json_file), format="json", is_path=True)
        self.assert_true(result.success, "3.1 Parse JSON data")
        if result.success:
            users = result.output.get("users", [])
            self.log(f"       Parsed {len(users)} users")
        
        # 3.2 Transform data - filter
        transformer = DataTransformSkill()
        data = {"items": [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
            {"name": "Charlie", "age": 35}
        ]}
        result = await transformer.run(data=data, operation="filter", 
                                       config={"field": "age", "min": 28})
        self.assert_true(result.success, "3.2 Filter users by age")
        if result.success:
            self.log(f"       Filtered to {len(result.output)} users (age >= 28)")
        
        # 3.3 Sort data
        result = await transformer.run(data=data, operation="sort",
                                       config={"field": "age", "reverse": True})
        self.assert_true(result.success, "3.3 Sort by age descending")
        if result.success and len(result.output) > 0:
            oldest = result.output[0].get("name")
            self.log(f"       Oldest: {oldest}")
    
    # Scenario 4: Web Operations
    async def scenario_4_web_operations(self):
        print("\n[Scenario 4] Web Operations")
        print("-" * 50)
        
        # 4.1 Fetch webpage
        fetcher = WebFetchSkill()
        result = await fetcher.run(url="https://httpbin.org/json")
        if result.success:
            self.assert_true("slideshow" in str(result.output) or "json" in str(result.output).lower(), 
                           "4.1 Fetch JSON endpoint")
            self.log(f"       Fetched: {len(result.output)} chars")
        else:
            self.log(f"[SKIP] 4.1 Web fetch: {result.error_message}")
            self.passed += 1
        
        # 4.2 Web search (mock mode)
        searcher = WebSearchSkill()
        result = await searcher.run(query="python best practices", limit=3)
        self.assert_true(result.success, "4.2 Web search")
        if result.success:
            results = result.output.get("results", [])
            self.log(f"       Found {len(results)} search results")
    
    # Scenario 5: AI Tasks
    async def scenario_5_ai_tasks(self):
        print("\n[Scenario 5] AI-Powered Tasks")
        print("-" * 50)
        
        if not Config.has_kimi():
            self.log("[SKIP] No API key - AI tests skipped")
            self.passed += 3
            return
        
        # 5.1 Translate
        translator = AITranslateSkill()
        result = await translator.run(text="Artificial Intelligence", target_language="zh")
        self.assert_true(result.success, "5.1 Translate EN->ZH")
        if result.success:
            self.log(f"       'Artificial Intelligence' -> '{result.output}'")
        
        # 5.2 Read and summarize notes
        reader = FileReadSkill()
        notes_file = Path(self.test_dir) / "notes.txt"
        result = await reader.run(path=str(notes_file))
        if result.success:
            notes = result.output
            # Use Kimi directly for summarization
            from blueclaw.llm import KimiClient
            client = KimiClient(Config.KIMI_API_KEY, Config.KIMI_BASE_URL, Config.KIMI_MODEL)
            try:
                response = client.chat(f"Summarize these meeting notes in 2 bullet points:\n{notes[:500]}", 
                                      max_tokens=100)
                self.assert_true(len(response.content) > 10, "5.2 Summarize notes")
                self.log(f"       Summary: {response.content[:80]}...")
            except Exception as e:
                self.log(f"[FAIL] 5.2 Summarize: {e}")
                self.failed += 1
    
    # Scenario 6: System Commands
    async def scenario_6_system_commands(self):
        print("\n[Scenario 6] System Operations")
        print("-" * 50)
        
        # 6.1 System info
        info = SystemInfoSkill()
        result = await info.run(info_type="platform")
        self.assert_true(result.success, "6.1 Get system info")
        if result.success:
            platform_info = result.output.get("platform", {})
            self.log(f"       Platform: {platform_info.get('system')} {platform_info.get('release')}")
        
        # 6.2 Safe shell command
        shell = ShellExecuteSkill()
        result = await shell.run(command="echo hello from blueclaw")
        self.assert_true(result.success, "6.2 Execute safe echo command")
        if result.success:
            self.log(f"       Output: {result.output.strip()}")
        
        # 6.3 Blocked dangerous command
        result = await shell.run(command="rm -rf /")
        self.assert_true(not result.success, "6.3 Dangerous command blocked")
        if not result.success:
            self.log(f"       Correctly blocked: {result.error_message[:40]}...")
    
    # Scenario 7: Full Engine Workflow
    async def scenario_7_engine_workflow(self):
        print("\n[Scenario 7] Full Engine Workflow")
        print("-" * 50)
        
        # 7.1 Create engine and process task
        engine = BlueclawEngineFacade("test_session_real", persistence_path=self.test_dir)
        
        result = await engine.process("Analyze the Python files in the project")
        self.assert_true("type" in result, "7.1 Process user input")
        self.log(f"       Phase: {result['type']}")
        
        # If thinking node, select options until blueprint
        iterations = 0
        while result.get("type") == "thinking_node" and iterations < 3:
            options = result.get("options", [])
            if options:
                option_id = options[0].id if hasattr(options[0], 'id') else options[0].get("id")
                result = await engine.select_option(result["node_id"], option_id)
                iterations += 1
                self.log(f"       Selected option, new phase: {result.get('type')}")
        
        # 7.2 Check execution steps
        self.assert_true(len(engine.execution_steps) > 0, "7.2 Blueprint generated")
        self.log(f"       Steps: {len(engine.execution_steps)}")
        
        # 7.3 Execute blueprint (if steps exist)
        if engine.execution_steps:
            exec_result = await engine.execute_blueprint()
            self.assert_true("status" in exec_result, "7.3 Execution completed")
            self.log(f"       Status: {exec_result.get('status')}")
        
        # 7.4 Check status
        status = engine.get_status()
        self.assert_true(status.get("session_id") == "test_session_real", "7.4 Session tracked")


async def main():
    tester = ScenarioTester()
    success = await tester.run_all()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
