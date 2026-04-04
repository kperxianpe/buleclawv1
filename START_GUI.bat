@echo off
chcp 65001 >nul
echo Starting Blueclaw v1.0 GUI (Fixed Version)...
echo.
python run_fixed_gui.py
if errorlevel 1 (
    echo.
    echo Error: Failed to start GUI
    echo Please make sure PyQt5 is installed:
    echo   pip install PyQt5
    pause
)
