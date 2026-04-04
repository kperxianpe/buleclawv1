#!/usr/bin/env python3
"""
run_gui.py - Start Blueclaw v1.0 PyQt5 GUI
"""

import sys
from pathlib import Path

# Check Python version
if sys.version_info < (3, 7):
    print("Error: Python 3.7+ required")
    sys.exit(1)

try:
    from PyQt5.QtWidgets import QApplication
    print("PyQt5 check: OK")
except ImportError as e:
    print(f"PyQt5 not found: {e}")
    print("Install with: pip install PyQt5")
    sys.exit(1)

# Start GUI
from blueclaw_v1_gui import main

if __name__ == "__main__":
    print("Starting Blueclaw v1.0 GUI...")
    main()
