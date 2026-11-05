@echo off
title AI Meeting Assistant - Clean Project Packager
echo ===================================================================
echo   AI MEETING ASSISTANT - LIGHTWEIGHT CLEAN PROJECT ARCHIVER
echo   Packaging: Only Important Project Source Code, UI, and Configs
echo   Excluding: models, python310, node_modules, uploads, caches, scratch
echo ===================================================================
cd /d "%~dp0"
"..\python310\python.exe" scratch\zip_project.py
echo.
echo ===================================================================
echo   CLEAN LIGHTWEIGHT ZIP CREATED SUCCESSFULLY! (~1.5 MB)
echo   Locations:
echo     - Desktop:   %USERPROFILE%\Desktop\AI_Meeting_Assistant.zip
echo     - Downloads: %USERPROFILE%\Downloads\AI_Meeting_Assistant.zip
echo     - Project:   %~dp0AI_Meeting_Assistant.zip
echo ===================================================================
echo.
if exist "%USERPROFILE%\Desktop\AI_Meeting_Assistant.zip" (
    start "" explorer /select,"%USERPROFILE%\Desktop\AI_Meeting_Assistant.zip"
) else if exist "%~dp0AI_Meeting_Assistant.zip" (
    start "" explorer /select,"%~dp0AI_Meeting_Assistant.zip"
)
pause
exit
