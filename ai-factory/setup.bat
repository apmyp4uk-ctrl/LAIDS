@echo off
REM AI Factory Setup Script for Windows
REM This script checks prerequisites and sets up the AI Factory system

echo ========================================
echo AI Factory - Setup Script
echo ========================================
echo.

REM Create logs directory
if not exist "logs" mkdir logs

echo [1/10] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.12+ from python.org
    echo Press any key to exit...
    pause >nul
    exit /b 1
)
python --version
echo [OK] Python found

echo [2/10] Checking Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo Git not found. Please install Git from git-scm.com
    echo Press any key to exit...
    pause >nul
    exit /b 1
)
git --version
echo [OK] Git found

echo [3/10] Checking NVIDIA GPU...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo WARNING: NVIDIA GPU not detected
) else (
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
    echo [OK] GPU found
)

echo [4/10] Checking RAM...
for /f "tokens=3" %%a in ('systeminfo ^| find "Total Physical Memory"') do set RAM=%%a
echo Available RAM: %RAM%
echo [OK] RAM checked

echo [5/10] Checking disk space...
for /f "tokens=3" %%a in ('dir /-c ^| find "bytes free"') do set FREE=%%a
echo Free disk space: %FREE%
echo [OK] Disk space checked

echo [6/10] Creating project directories...
if not exist "agents" mkdir agents
if not exist "configs" mkdir configs
if not exist "logs" mkdir logs
if not exist "utils" mkdir utils
echo [OK] Directories created

echo [7/10] Installing Python dependencies...
pip install -q uv
pip install -q openhands ollama prometheus-client pyyaml python-dotenv
echo [OK] Dependencies installed

echo [8/10] Creating .env file...
if not exist ".env" (
    copy .env.example .env
    echo .env file created - please add your API keys
)
echo [OK] Environment configured

echo [9/10] Setting up autostart...
schtasks /create /tn "AI Factory" /tr "%~dp0run.bat" /sc onlogon /f >nul 2>&1
if errorlevel 1 (
    echo Warning: Could not create autostart task
) else (
    echo [OK] Autostart configured
)

echo [10/10] Setup complete!
echo.
echo ========================================
echo Next steps:
echo 1. Add your API keys to .env
echo 2. Start Ollama: ollama serve
echo 3. Pull models: ollama pull mistral
echo 4. Run: run.bat
echo ========================================

echo.
echo Press any key to exit...
pause >nul