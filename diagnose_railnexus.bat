@echo off
setlocal
cd /d "%~dp0"
title RailNexus Diagnostic
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"
echo RailNexus Diagnostic
echo ==================
echo.
where python
echo.
python --version
echo.
where node
echo.
node --version
echo.
npm --version
echo.
if exist "%PY%" (
  echo Virtual environment Python:
  "%PY%" --version
) else echo Virtual environment not created yet.
echo.
echo Press any key to close.
pause >nul
