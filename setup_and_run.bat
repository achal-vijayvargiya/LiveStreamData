@echo off
echo ========================================
echo LiveStreamData Application Setup
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo ✅ Python found
python --version

:: Check if virtual environment exists
if not exist "venv\" (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

:: Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment activated

:: Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip
echo ✅ Pip upgraded

:: Install requirements
echo.
echo Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)
echo ✅ Requirements installed

:: Install Playwright browsers
echo.
echo Installing Playwright browsers...
playwright install chromium
if errorlevel 1 (
    echo ERROR: Failed to install Playwright browsers
    pause
    exit /b 1
)
echo ✅ Playwright browsers installed

:: Check if configuration files exist
echo.
echo Checking configuration files...
if not exist "app\config\users.json" (
    echo ERROR: app\config\users.json not found
    echo Please ensure your configuration files are in place
    pause
    exit /b 1
)
echo ✅ Configuration files found

:: Check if credentials exist
if not exist "app\credentials\service_account.json" (
    echo WARNING: app\credentials\service_account.json not found
    echo OCR functionality may not work without Google Cloud credentials
)

echo.
echo ========================================
echo Starting Application...
echo ========================================
echo.

:: Start WebSocket server in background
echo Starting WebSocket server...
start "WebSocket Server" cmd /k "call venv\Scripts\activate.bat && python app\websocket\server.py"

:: Wait a moment for WebSocket server to start
timeout /t 3 /nobreak >nul

:: Start main application
echo Starting main application...
python main.py

echo.
echo ========================================
echo Application stopped
echo ========================================
pause 