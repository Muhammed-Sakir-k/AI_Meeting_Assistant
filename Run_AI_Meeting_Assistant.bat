@echo off
title AI Meeting Assistant Launcher
echo ===================================================
echo   Starting AI Meeting Assistant Backend Server...
echo ===================================================
cd /d "%~dp0"

set "PY=python"
if exist "python310\python.exe" (
    set "PY=python310\python.exe"
) else if exist "..\python310\python.exe" (
    set "PY=..\python310\python.exe"
)

start "AI Meeting Assistant Backend" %PY% main.py
echo Waiting 4 seconds for the server to initialize...
timeout /t 4 /nobreak > nul
echo ===================================================
echo   Opening Dashboard in Browser...
echo ===================================================
start "" "http://127.0.0.1:8080"
echo Done. You can close this window. Keep the backend window open while using the app!
timeout /t 2 > nul
exit
