@echo off
title AI Meeting Assistant DB Resetter
echo ===================================================
echo   Clearing database tables...
echo ===================================================
cd /d "%~dp0"
..\python310\python.exe scratch\reset_db.py
echo ===================================================
echo   Finished database reset!
echo ===================================================
pause
