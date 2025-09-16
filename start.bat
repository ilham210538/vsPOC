@echo off
echo 🚀 Starting Calendar Agent Web Application...
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 18+ first.
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo ❌ .env file not found. Please create .env with your Azure credentials.
    echo    Copy your existing .env file from the previous terminal project.
    pause
    exit /b 1
)

echo ✅ Node.js found: 
node --version

echo ✅ Python found:
python --version

echo.
echo 📦 Installing Node.js dependencies...
call npm install
if errorlevel 1 (
    echo ❌ Failed to install Node.js dependencies
    pause
    exit /b 1
)

echo.
echo 🔧 Installing Python dependencies...
call .venv\Scripts\activate
pip install -r req.txt
if errorlevel 1 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo 🏗️ Building React frontend...
call npm run build
if errorlevel 1 (
    echo ❌ Failed to build React frontend
    pause
    exit /b 1
)

echo.
echo ✅ Setup complete! Starting the application...
echo 📱 Open http://localhost:3000 in your browser
echo 🛑 Press Ctrl+C to stop the server
echo.

REM Start the server
call npm start
