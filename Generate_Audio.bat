@echo off
title AI Meeting Assistant Audio Generator
echo ===================================================
echo   Generating Test Meeting Audio File...
echo ===================================================
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File generate_meeting_audio.ps1
echo ===================================================
echo   Finished!
echo ===================================================
pause
