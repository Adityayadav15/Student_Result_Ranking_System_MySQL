@echo off
title MeritBoard - Student Result Ranking System
cd /d "%~dp0"
echo Make sure .env exists and contains your MySQL password.
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo Dependency installation failed.
  pause
  exit /b 1
)
py app.py
pause
