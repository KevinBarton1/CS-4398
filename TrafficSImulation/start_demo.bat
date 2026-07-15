@echo off
setlocal
cd /d "%~dp0"
echo Starting TrafficScope...
where py >nul 2>nul
if %errorlevel%==0 (
  start "" http://127.0.0.1:8000
  py -3 main.py
  goto :end
)
where python >nul 2>nul
if %errorlevel%==0 (
  start "" http://127.0.0.1:8000
  python main.py
  goto :end
)
where node >nul 2>nul
if %errorlevel%==0 (
  start "" http://127.0.0.1:8000
  node tools\dev-server.js
  goto :end
)
echo Python 3 or Node.js is required to run TrafficScope.
pause
:end
