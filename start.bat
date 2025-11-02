@echo off
chcp 65001
echo ================================================================
echo Smart Dashboard - Launching Application
echo ================================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo.
    powershell -Command "Write-Host '[ERROR] Installation not found!' -ForegroundColor Red -BackgroundColor Black"
    echo.
    powershell -Command "Write-Host 'Required Action:' -ForegroundColor Yellow"
    echo 1. Double-click on "setup.bat" to install the application
    echo 2. Wait for setup to complete successfully
    echo 3. Then run "start.bat" again
    echo.
    powershell -Command "Write-Host 'You must run setup.bat before starting the application.' -ForegroundColor Red"
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/2] Loading environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo.
    powershell -Command "Write-Host '[ERROR] Failed to load environment!' -ForegroundColor Red -BackgroundColor Black"
    echo.
    powershell -Command "Write-Host 'Solution:' -ForegroundColor Yellow"
    echo 1. Delete the 'venv' folder in this directory
    echo 2. Run "setup.bat" to reinstall
    echo 3. Then run "start.bat" again
    echo.
    powershell -Command "Write-Host 'The installation may be corrupted.' -ForegroundColor Red"
    echo.
    pause
    exit /b 1
)

REM Check if Streamlit is installed
echo [2/2] Checking components...
streamlit --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    powershell -Command "Write-Host '[ERROR] Required components not found!' -ForegroundColor Red -BackgroundColor Black"
    echo.
    powershell -Command "Write-Host 'Solution:' -ForegroundColor Yellow"
    echo 1. Run "setup.bat" to install missing components
    echo 2. Wait for installation to complete
    echo 3. Then run "start.bat" again
    echo.
    powershell -Command "Write-Host 'Critical components are missing from the installation.' -ForegroundColor Red"
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================================
echo Starting Smart Dashboard...
echo ================================================================
echo.
echo The application will open in your browser automatically
echo.
echo Dashboard URL: http://localhost:8501
echo.
echo IMPORTANT:
echo - Keep this window open while using the application
echo - To stop the application: Press Ctrl+C or close this window
echo - To restart: Run start.bat again
echo ================================================================
echo.

REM Wait 3 seconds for user to read the message
timeout /t 3 /nobreak >nul

REM Start Streamlit
echo Launching...
echo.
streamlit run upload.py --server.port 8501 --server.address localhost

echo.
echo ================================================================
echo Application has stopped
echo ================================================================
echo.
echo Press any key to close this window...
pause >nul