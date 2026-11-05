@echo off
title AI Meeting Assistant DB Inspector
echo ===================================================
echo   Inspecting database tables...
echo ===================================================
cd /d "%~dp0"
..\python310\python.exe scratch\check_db.py
echo ===================================================
echo   Done! Results written to scratch\db_results.txt
echo ===================================================
pause
