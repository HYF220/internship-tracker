@echo off
title Internship Tracker - Stopping

echo ========================================
echo   Stopping All Services
echo ========================================
echo.

set "PATH=D:\pgsql\pgsql\bin;%PATH%"

echo Stopping PostgreSQL...
pg_ctl -D D:\pgdata stop 2>nul
echo PostgreSQL stopped

echo.
echo Stopping Backend...
taskkill /f /im uvicorn.exe >nul 2>&1
echo Backend stopped

echo Stopping Frontend...
taskkill /f /im node.exe >nul 2>&1
echo Frontend stopped

echo.
echo All done.
pause
