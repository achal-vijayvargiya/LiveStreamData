@echo off
echo ========================================
echo LiveStreamData Application Runner
echo ========================================
echo.

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    echo Please run setup_and_run.bat first to set up the environment
    pause
    exit /b 1
)

:: Start WebSocket server in background
echo Starting WebSocket server...
start "WebSocket Server" cmd /k "call venv\Scripts\activate.bat && python app\websocket\server.py"

:: Wait a moment for WebSocket server to start
echo Waiting for WebSocket server to start...
timeout /t 3 /nobreak >nul

:: Start main application
echo Starting main application...
python main.py

echo.
echo ========================================
echo Application stopped
echo ========================================
pause 