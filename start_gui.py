#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
start_gui.py - Start Blueclaw v1.0 GUI

Usage:
    python start_gui.py
"""

import sys
from pathlib import Path

# Check Python version
if sys.version_info < (3, 7):
    print("Error: Python 3.7+ required")
    sys.exit(1)

try:
    import tkinter as tk
except ImportError:
    print("Error: tkinter not available")
    print("Please install tkinter for your Python version")
    sys.exit(1)

# Start GUI
from gui_launcher import main

if __name__ == "__main__":
    print("Starting Blueclaw v1.0 GUI...")
    main()
