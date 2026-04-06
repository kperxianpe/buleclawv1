#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Checker

Verify Blueclaw configuration and API keys
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from blueclaw.config import Config
from blueclaw.skills import SkillRegistry


def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)


def check_env_file():
    """Check if .env file exists"""
    env_path = Path(".env")
    example_path = Path(".env.example")
    
    print_section("Environment File")
    
    if env_path.exists():
        print("[OK] .env file found")
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        key_count = sum(1 for line in lines if '=' in line and not line.startswith('#'))
        print(f"  Contains {key_count} configuration entries")
    else:
        print("[FAIL] .env file NOT found")
        if example_path.exists():
            print("  -> Copy .env.example to .env and fill in your API keys")
        else:
            print("  -> Create .env file with your API keys")
        return False
    
    return True


def check_api_keys():
    """Check API key configuration"""
    print_section("API Keys")
    
    status = Config.check_setup()
    
    if status['kimi_ready']:
        print("[OK] Kimi (Moonshot) API key configured")
        print(f"  Model: {Config.KIMI_MODEL}")
        print(f"  Base URL: {Config.KIMI_BASE_URL}")
    else:
        print("[FAIL] Kimi API key NOT configured")
        print("  -> Add KIMI_API_KEY to .env file")
    
    if status['openai_ready']:
        print("[OK] OpenAI API key configured (fallback)")
    
    if not status['llm_available']:
        print("\n[!] No LLM API configured - AI skills will use mock mode")
    
    return status['llm_available']


def check_skills():
    """Check registered skills"""
    print_section("Skills")
    
    total = SkillRegistry.count()
    print(f"Total registered skills: {total}")
    
    categories = SkillRegistry.get_categories()
    for cat in categories:
        count = len(SkillRegistry.list_by_category(cat))
        print(f"  {cat}: {count} skills")
    
    return total >= 15


def test_kimi_connection():
    """Test Kimi API connection if key is available"""
    if not Config.has_kimi():
        return False
    
    print_section("Kimi API Connection Test")
    
    try:
        from blueclaw.llm import KimiClient
        
        client = KimiClient(
            api_key=Config.KIMI_API_KEY,
            base_url=Config.KIMI_BASE_URL,
            model=Config.KIMI_MODEL
        )
        
        print("Testing API connection...")
        response = client.chat("Hello, respond with 'Kimi API OK' only", max_tokens=50)
        
        if "OK" in response.content or "ok" in response.content.lower():
            print("[OK] Kimi API connection successful")
            print(f"  Response: {response.content[:50]}...")
            print(f"  Tokens used: {response.usage.get('total_tokens', 'N/A')}")
            return True
        else:
            print(f"✗ Unexpected response: {response.content[:50]}")
            return False
            
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def main():
    print("")
    print("#" * 60)
    print("#" + "Blueclaw Setup Checker".center(58) + "#")
    print("#" + "Week 17 - Skills + LLM Integration".center(58) + "#")
    print("#" * 60)
    print("")
    
    results = []
    
    # Check .env file
    results.append(("Environment file", check_env_file()))
    
    # Check API keys
    results.append(("API Keys", check_api_keys()))
    
    # Check skills
    results.append(("Skills", check_skills()))
    
    # Test connection (optional)
    if Config.has_kimi():
        results.append(("Kimi Connection", test_kimi_connection()))
    
    # Summary
    print_section("Summary")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {name}")
    
    print("\n" + "="*60)
    
    if passed == total:
        print("All checks passed! Ready to use.")
        return 0
    else:
        print("[!] Some checks failed. Please fix the issues above.")
        print("\nQuick start:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your KIMI_API_KEY to .env")
        print("  3. Run this script again")
        return 1


if __name__ == "__main__":
    sys.exit(main())
