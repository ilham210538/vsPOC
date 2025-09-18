@echo off
echo Visual Solutions POC - Deploy Script
echo ===================================
echo.

echo 1. Building frontend...
call npm run build

if %errorlevel% neq 0 (
    echo ❌ Frontend build failed!
    pause
    exit /b 1
)

echo.
echo 2. Adding built files to git...
git add public/

echo.
echo 3. Checking git status...
git status

echo.
echo ✅ Ready to deploy!
echo.
echo Next steps:
echo   git commit -m "Update frontend"
echo   git push
echo.
pause
