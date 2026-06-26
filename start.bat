@echo off
setlocal
title Internship Tracker - Starting

echo ========================================
echo   Internship Tracker - One Click Start
echo ========================================
echo.
echo NOTE: Using Neon cloud database.
echo       Make sure backend\.env has your DATABASE_URL.
echo.

cd /d "D:\实习投递管理系统"

echo [1/2] Starting Backend API on port 8000...
start "Backend-API" cmd /c "cd /d D:\实习投递管理系统\backend && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload && pause"
echo        Backend window opened

:: Wait for backend to be ready
ping -n 5 127.0.0.1 >nul

echo.
echo [2/2] Starting Frontend on port 5173...
start "Frontend" cmd /c "cd /d D:\实习投递管理系统\frontend && npm run dev && pause"
echo        Frontend window opened

ping -n 4 127.0.0.1 >nul

echo.
echo Opening browser...
start http://localhost:5173

echo.
echo ========================================
echo   All done!
echo   Frontend : http://localhost:5173
echo   Backend  : http://localhost:8000
echo   API Docs : http://localhost:8000/docs
echo ========================================
echo.
echo Close the Backend/Frontend windows to stop all.
echo This window can be closed.
pause
