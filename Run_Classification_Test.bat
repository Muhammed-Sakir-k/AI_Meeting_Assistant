@echo off
title AI Meeting Assistant Classifier Test
echo ===================================================
echo   Running zero-shot classification test...
echo ===================================================
cd /d "%~dp0"
..\python310\python.exe scratch\test_classification.py > scratch\classification_results.txt
echo ===================================================
echo   Done! Results written to scratch\classification_results.txt
echo ===================================================
pause
