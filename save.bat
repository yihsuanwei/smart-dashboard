@echo off
chcp 65001 >nul
echo ========================================
echo   Smart Dashboard - 儲存變更到 GitHub
echo ========================================
echo.

echo [1/4] 檢查變更...
git status --short
echo.

set /p confirm="確定要儲存這些變更嗎？(Y/N): "
if /i not "%confirm%"=="Y" (
    echo 已取消
    pause
    exit /b 0
)
echo.

echo [2/4] 加入變更...
git add -A
echo.

set /p msg="請輸入變更說明 (直接按 Enter 使用預設): "
if "%msg%"=="" set msg=Update Smart Dashboard

echo.
echo [3/4] 建立存檔點...
git commit -m "%msg%"
if errorlevel 1 (
    echo.
    echo 沒有變更需要儲存，或發生錯誤
    pause
    exit /b 1
)
echo.

echo [4/4] 上傳到 GitHub...
git push
if errorlevel 1 (
    echo.
    echo 上傳失敗，請確認網路連線
    pause
    exit /b 1
)

echo.
echo ========================================
echo   儲存完成！變更已上傳到 GitHub
echo ========================================
pause
