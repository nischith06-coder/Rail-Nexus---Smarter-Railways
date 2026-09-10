@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title RailNexus - Smarter Railways
set "ROOT=%~dp0"
set "PY=%ROOT%.venv\Scripts\python.exe"
set "LOG=%ROOT%railnexus_startup.log"

echo ============================================================
echo              RAILNEXUS - SMARTER RAILWAYS
echo              SIH26028 ^| ONE-CLICK DEMO
 echo ============================================================
>"%LOG%" echo RailNexus startup %date% %time%

if not exist "%PY%" (
 echo [1/5] Creating Python environment...
 py -m venv "%ROOT%.venv" >>"%LOG%" 2>&1
 if errorlevel 1 goto fail
) else echo [1/5] Python environment ready.

"%PY%" -c "import fastapi,uvicorn,pandas,numpy,sklearn,joblib; print('Backend packages OK')" >>"%LOG%" 2>&1
if errorlevel 1 (
 echo [2/5] Installing backend dependencies...
 "%PY%" -m pip install -r "%ROOT%backend\requirements.txt" >>"%LOG%" 2>&1
 if errorlevel 1 goto fail
) else echo [2/5] Backend packages ready.

echo [3/5] Preparing 2,000-train fleet and ETA model...
"%PY%" "%ROOT%backend\scripts\generate_demo_data.py" >>"%LOG%" 2>&1
if errorlevel 1 goto fail
if not exist "%ROOT%backend\models\eta_model.joblib" "%PY%" "%ROOT%backend\scripts\train_model.py" >>"%LOG%" 2>&1
if errorlevel 1 goto fail

echo [4/5] Starting RailNexus backend + dashboard...
rem Always restart the RailNexus process on port 8000 so a previous project
rem version cannot remain active and cause stale route/UI data.
powershell -NoProfile -Command "$c=Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue|Select-Object -First 1;if($c){$p=Get-CimInstance Win32_Process -Filter ('ProcessId = '+$c.OwningProcess);if($p.CommandLine -match 'python|uvicorn|train-eta'){Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue;Start-Sleep -Milliseconds 700}}" >nul 2>nul
start "RailNexus Backend - KEEP OPEN" /D "%ROOT%backend" cmd /k ""%PY%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

set /a WAIT=0
:wait
set /a WAIT+=1
timeout /t 1 /nobreak >nul
powershell -NoProfile -Command "try{$r=Invoke-WebRequest -UseBasicParsing 'http://127.0.0.1:8000/health' -TimeoutSec 2;if($r.Content -match 'RailNexus'){exit 0}else{exit 1}}catch{exit 1}" >nul 2>nul
if not errorlevel 1 goto ready
if %WAIT% GEQ 30 goto fail
 goto wait

:ready
echo [5/5] Starting built-in live telemetry engine...
echo.
echo ============================================================
echo                 RAILNEXUS IS READY
 echo Dashboard : http://127.0.0.1:8000/
echo API Docs  : http://127.0.0.1:8000/docs
echo Fleet     : 2,000 simulated trains
echo ============================================================
start "" "http://127.0.0.1:8000/?railnexus=%RANDOM%"
echo.
echo Leave the Backend window open. The live telemetry engine runs inside it.
pause
exit /b 0

:fail
echo.
echo ERROR: startup failed. Open railnexus_startup.log for details.
echo The window will remain open so the error can be read.
pause
exit /b 1
