@echo off
title AI Meeting Assistant Restart Helper
echo ===================================================
echo   Stopping any existing backend server on port 8000...
echo ===================================================
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000') do (
    echo Found process %%a using port 8000. Terminating...
    taskkill /f /pid %%a >nul 2>&1
)
timeout /t 2 /nobreak > nul

echo ===================================================
echo   Disabling pre-compiled build to force fresh source...
echo ===================================================
cd /d "%~dp0"
if exist "frontend\dist" (
    echo Renaming frontend\dist to frontend\dist_disabled...
    ren "frontend\dist" "dist_disabled"
)

echo ===================================================
echo   Launching backend server...
echo ===================================================
start "AI Meeting Assistant Backend" "..\python310\python.exe" main.py
echo Waiting 5 seconds for initialization...
timeout /t 5 /nobreak > nul

echo ===================================================
echo   Opening dashboard in browser...
echo ===================================================
start "" "http://127.0.0.1:8000"
echo Done! Please check the dashboard now.
timeout /t 2 > nul
exit
