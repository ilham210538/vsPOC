@echo off
echo Visual Solutions POC - Full Development Environment
echo ==================================================

echo.
echo This script will:
echo 1. Install frontend dependencies
echo 2. Build the frontend
echo 3. Start the complete application
echo.
echo 1. Installing frontend dependencies...
cd frontend
call npm install

if %errorlevel% neq 0 (
    echo Error: Failed to install frontend dependencies
    pause
    exit /b 1
)

echo.
echo 2. Building frontend...
call npm run build

if %errorlevel% neq 0 (
    echo Error: Failed to build frontend
    pause
    exit /b 1
)

cd ..

echo.
echo 3. Starting complete application...
echo Application available at: http://localhost:8080
echo API available at: http://localhost:8080/api
echo.
echo Press Ctrl+C to stop the server
call npm start
