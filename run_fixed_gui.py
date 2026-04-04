#!/usr/bin/env python3
"""
run_fixed_gui.py - Start Blueclaw v1.0 GUI (Thread-Safe Version)

This version fixes the crash issue when processing messages.
All GUI updates are now thread-safe.
"""

import sys

print("Starting Blueclaw v1.0 GUI (Fixed Version)...")
print("=" * 60)

# Check Python version
if sys.version_info < (3, 7):
    print("Error: Python 3.7+ required")
    sys.exit(1)

try:
    from PyQt5.QtWidgets import QApplication
    print("[OK] PyQt5 available")
except ImportError as e:
    print(f"[ERROR] PyQt5 not found: {e}")
    print("Install with: pip install PyQt5")
    sys.exit(1)

# Start the fixed GUI
from blueclaw_v1_gui_fixed import main

if __name__ == "__main__":
    main()
