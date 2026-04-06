#!/usr/bin/env python3
import asyncio
from blueclaw.skills import DataParseSkill, ShellExecuteSkill

async def test_json():
    print("=== Testing JSON Parse ===")
    skill = DataParseSkill()
    
    # Test inline JSON
    result = await skill.run(source='{"users": [{"name": "Alice"}]}', format='json', is_path=False)
    print(f"Success: {result.success}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error_message}")

async def test_shell():
    print("\n=== Testing Shell ===")
    skill = ShellExecuteSkill()
    
    # Test echo
    result = await skill.run(command="echo hello")
    print(f"Success: {result.success}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error_message}")

asyncio.run(test_json())
asyncio.run(test_shell())
