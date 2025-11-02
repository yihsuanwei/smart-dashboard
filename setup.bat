@echo off
setlocal enabledelayedexpansion
chcp 65001
echo ================================================================
echo Smart Dashboard - Initial Setup
echo ================================================================
echo.
echo This will automatically install all required components
echo Estimated time: 2-3 minutes. Please wait...
echo.

REM Auto-detect compatible Python version
echo [Step 1/4] Checking for compatible Python version...

set PYTHON_CMD=python

REM Check default python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    python -c "import sys; exit(0 if sys.version_info[:3] == (3, 13, 2) else 1)" 2>nul
    if %errorlevel% equ 0 (
        goto :python_found
    )
)

REM Try py launcher to find compatible version
py -0 >nul 2>&1
if %errorlevel% equ 0 (
    echo Searching for Python 3.13.2...
    py -3.13 -c "import sys; exit(0 if sys.version_info[:3] == (3, 13, 2) else 1)" >nul 2>&1
    if !errorlevel! equ 0 (
        set PYTHON_CMD=py -3.13
        powershell -Command "Write-Host 'Found Python 3.13.2' -ForegroundColor Green"
        goto :python_found
    )
)

REM No compatible Python found
echo.
powershell -Command "Write-Host '[ERROR] No compatible Python version found!' -ForegroundColor Red -BackgroundColor Black"
echo.
python --version 2>nul
if %errorlevel% equ 0 (
    python --version
    echo.
    powershell -Command "Write-Host 'Your Python version is not compatible (requires 3.13.2)' -ForegroundColor Yellow"
) else (
    powershell -Command "Write-Host 'Python is not installed' -ForegroundColor Yellow"
)
echo.
echo Please install Python 3.13.2 from: https://python.org
echo During installation, CHECK the box "Add Python to PATH"
echo.
powershell -Command "Write-Host 'You can install multiple Python versions - they will coexist.' -ForegroundColor Cyan"
echo.
pause
exit /b 1

:python_found

echo [OK] Using Python:
%PYTHON_CMD% --version
echo.

REM Check if venv already exists
echo.
echo [Step 2/4] Setting up Python environment...
if exist "venv\" (
    powershell -Command "Write-Host '[OK] Virtual environment already exists - using existing installation' -ForegroundColor Green"
    echo.
    goto :install_packages
)

REM Create virtual environment
echo Creating isolated Python environment...
echo (This won't affect other Python programs on your computer)
%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo.
    powershell -Command "Write-Host '[ERROR] Failed to create virtual environment!' -ForegroundColor Red -BackgroundColor Black"
    echo.
    powershell -Command "Write-Host 'Solution:' -ForegroundColor Yellow"
    echo 1. Right-click on setup.bat
    echo 2. Select "Run as administrator"
    echo 3. Click "Yes" when prompted
    echo.
    powershell -Command "Write-Host 'Administrator rights are required for environment creation.' -ForegroundColor Red"
    echo.
    pause
    exit /b 1
)
powershell -Command "Write-Host '[OK] Virtual environment created successfully' -ForegroundColor Green"
echo.

:install_packages
REM Activate virtual environment
echo [Step 3/4] Activating environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo.
    powershell -Command "Write-Host '[ERROR] Failed to activate environment!' -ForegroundColor Red -BackgroundColor Black"
    echo.
    powershell -Command "Write-Host 'Possible Cause: Virtual environment is corrupted' -ForegroundColor Yellow"
    echo.
    powershell -Command "Write-Host 'Solution:' -ForegroundColor Yellow"
    echo 1. Close this window
    echo 2. Delete the 'venv' folder in this directory
    echo 3. Run setup.bat again
    echo.
    powershell -Command "Write-Host 'Note: If venv folder does not exist, try running as Administrator.' -ForegroundColor Cyan"
    echo.
    pause
    exit /b 1
)
powershell -Command "Write-Host '[OK] Environment activated successfully' -ForegroundColor Green"
echo.

REM Upgrade pip first
echo [Step 4/4] Installing required packages...
echo (This requires internet connection, please wait 1-2 minutes)
echo.
python -m pip install --upgrade pip --quiet

REM Install all packages from requirements.txt (only use precompiled binaries)
echo Installing packages (using precompiled versions only)...
pip install --only-binary :all: -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    powershell -Command "Write-Host '[ERROR] Package installation failed!' -ForegroundColor Red -BackgroundColor Black"
    echo.
    powershell -Command "Write-Host 'This usually means a package does not have a precompiled version for your Python version.' -ForegroundColor Yellow"
    echo.
    powershell -Command "Write-Host 'Solution: Delete venv folder and run setup.bat again' -ForegroundColor Yellow"
    echo If the problem persists, your Python version may not be compatible.
    echo.
    goto :error
)

REM Verify streamlit installation
echo.
echo Verifying installation...
streamlit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Verification failed!
    goto :error
)

echo.
echo ================================================================
echo Setup Complete!
echo ================================================================
echo.
echo All components have been installed successfully!
echo.
echo Next Step: Double-click "start.bat" to launch the application
echo.
pause
exit /b 0

:error
echo.
pause
exit /b 1
