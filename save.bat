@echo off
echo ========================================
echo   Smart Dashboard - Save to GitHub
echo ========================================
echo.

echo [1/4] Checking changes...
git status --short
echo.

set /p confirm="Save these changes? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo Cancelled
    pause
    exit /b 0
)
echo.

echo [2/4] Staging changes...
git add -A
echo.

set /p msg="Enter commit message (press Enter for default): "
if "%msg%"=="" set msg=Update Smart Dashboard

echo.
echo [3/4] Creating commit...
git commit -m "%msg%"
if errorlevel 1 (
    echo.
    echo No changes to save, or error occurred
    pause
    exit /b 1
)
echo.

echo [4/4] Pushing to GitHub...
git push
if errorlevel 1 (
    echo.
    echo Push failed - check your network connection
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Done! Changes uploaded to GitHub
echo ========================================
pause
