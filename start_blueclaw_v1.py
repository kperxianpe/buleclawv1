#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Start Blueclaw v1.0 with Thinking Blueprint

Usage:
    python start_blueclaw_v1.py

Features:
    - Thinking Blueprint with intent recognition
    - Four-Option interactive mode
    - Dark theme UI
    - Execution Blueprint visualization
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 60)
    print("Blueclaw v1.0 - Starting with Thinking Blueprint")
    print("=" * 60)
    
    try:
        from blueclaw_v1_gui_with_thinking import main as gui_main
        gui_main()
    except Exception as e:
        print(f"\nError starting GUI: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
