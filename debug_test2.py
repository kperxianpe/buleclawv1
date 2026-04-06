#!/usr/bin/env python3
import asyncio
import tempfile
from pathlib import Path
from blueclaw.skills import DataParseSkill

async def test_json_file():
    print("=== Testing JSON Parse from File ===")
    skill = DataParseSkill()
    
    # Create temp file
    test_dir = tempfile.mkdtemp()
    json_file = Path(test_dir) / "test.json"
    json_file.write_text('{"users": [{"name": "Alice"}]}', encoding='utf-8')
    
    print(f"File path: {json_file}")
    print(f"File exists: {json_file.exists()}")
    print(f"File content: {json_file.read_text()}")
    
    result = await skill.run(path=str(json_file), format="json")
    print(f"Success: {result.success}")
    print(f"Output: {result.output}")
    print(f"Error: {result.error_message}")

asyncio.run(test_json_file())
