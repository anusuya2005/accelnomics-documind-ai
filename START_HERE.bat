@echo off
rem Double-click this file. It installs what is missing, sets everything up, and starts PrivateDocs AI.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_all.ps1"
echo.
pause