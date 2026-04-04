#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动 Blueclaw v1.0 + Thinking Blueprint GUI
"""

import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from blueclaw_v1_gui_thinking import main
    print("=" * 60)
    print("Blueclaw v1.0 - Thinking Blueprint Mode")
    print("=" * 60)
    print()
    print("Features:")
    print("  1. Intent Recognition with confidence")
    print("  2. Thinking Process visualization")
    print("  3. Four-Option UI (A/B/C/D)")
    print()
    main()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")
