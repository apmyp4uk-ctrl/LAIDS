@echo off
REM AI Factory - Run script for Windows
echo Starting AI Factory...
cd /d "%~dp0"
call .venv\Scripts\activate.bat 2>nul
python run.py
pause