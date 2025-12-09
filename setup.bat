@echo off
REM Discord AI Bot Setup Script for Windows
REM This script automates the setup process for the Discord AI Bot

setlocal enabledelayedexpansion

echo ================================================
echo   Discord AI Bot - Automated Setup
echo ================================================
echo.

REM Check if Docker is installed
echo [INFO] Checking if Docker is installed...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker first:
    echo   Visit: https://docs.docker.com/get-docker/
    exit /b 1
)
echo [SUCCESS] Docker is installed

REM Check if Docker is running
echo [INFO] Checking if Docker is running...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running. Please start Docker and try again.
    exit /b 1
)
echo [SUCCESS] Docker is running

REM Check if Python 3.8+ is installed
echo [INFO] Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.8 or higher:
    echo   Visit: https://www.python.org/downloads/
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python %PYTHON_VERSION% is installed

REM Note: Detailed version checking is complex in batch, assuming 3.8+ if Python 3 is installed
REM Users should verify they have Python 3.8+ manually if issues occur

REM Create virtual environment
echo [INFO] Creating Python virtual environment...
if exist "venv\" (
    echo [INFO] Virtual environment already exists, skipping creation
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    exit /b 1
)
echo [SUCCESS] Virtual environment activated

REM Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo [SUCCESS] pip upgraded

REM Install dependencies
echo [INFO] Installing dependencies from requirements.txt...
if not exist "requirements.txt" (
    echo [ERROR] requirements.txt not found!
    exit /b 1
)
pip install -r requirements.txt >nul
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)
echo [SUCCESS] Dependencies installed

REM Copy .env.example to .env if .env doesn't exist
echo [INFO] Setting up environment configuration...
if exist ".env" (
    echo [INFO] .env file already exists, skipping copy
) else (
    if not exist ".env.example" (
        echo [ERROR] .env.example not found!
        exit /b 1
    )
    copy .env.example .env >nul
    echo [SUCCESS] .env file created from .env.example
    echo [INFO] IMPORTANT: Please edit .env file and add your configuration values
)

REM Start Docker Compose
echo [INFO] Starting PostgreSQL with Docker Compose...
if not exist "docker-compose.yml" (
    echo [ERROR] docker-compose.yml not found!
    exit /b 1
)
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start Docker Compose
    exit /b 1
)
echo [SUCCESS] PostgreSQL container started

REM Wait for PostgreSQL to be ready
echo [INFO] Waiting for PostgreSQL to be ready...
timeout /t 5 /nobreak >nul
echo [SUCCESS] PostgreSQL should be ready

REM Run database setup script
echo [INFO] Initializing database...
if not exist "setup_db.py" (
    echo [ERROR] setup_db.py not found!
    exit /b 1
)
python setup_db.py
if errorlevel 1 (
    echo [ERROR] Failed to initialize database
    exit /b 1
)
echo [SUCCESS] Database initialized

echo.
echo ================================================
echo [SUCCESS] Setup completed successfully!
echo ================================================
echo.
echo Next steps:
echo   1. Edit the .env file and add your configuration:
echo      - DISCORD_BOT_TOKEN (from Discord Developer Portal)
echo      - OPENAI_API_KEY (from OpenAI)
echo      - GITHUB_TOKEN (from GitHub Settings)
echo.
echo   2. Activate the virtual environment (if not already active):
echo      venv\Scripts\activate.bat
echo.
echo   3. Start the Discord bot:
echo      python discord_bot.py
echo.
echo   4. To stop PostgreSQL later:
echo      docker-compose down
echo.
echo [INFO] For more information, see README.md

endlocal