@echo off
chcp 65001 >nul
echo ========================================
echo   Smart Dashboard - 更新並啟動
echo ========================================
echo.

echo [1/3] 正在檢查更新...
git pull
if errorlevel 1 (
    echo.
    echo ⚠️ 更新失敗，請確認網路連線或聯繫管理員
    pause
    exit /b 1
)
echo ✅ 更新完成
echo.

echo [2/3] 正在啟動環境...
call venv\Scripts\activate
if errorlevel 1 (
    echo.
    echo ⚠️ 環境啟動失敗，請先執行 setup.bat
    pause
    exit /b 1
)
echo ✅ 環境已啟動
echo.

echo [3/3] 正在啟動 Smart Dashboard...
echo.
echo ========================================
echo   Dashboard 網址: http://localhost:8501
echo   關閉方式: 按 Ctrl+C 或關閉此視窗
echo ========================================
echo.
streamlit run upload.py --server.port 8501 --server.address localhost

pause
