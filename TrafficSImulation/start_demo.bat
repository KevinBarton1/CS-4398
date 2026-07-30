@echo off
setlocal
cd /d "%~dp0"
echo Building TrafficScope 1.1...
if not exist "node_modules" call npm install
call npm run build
if errorlevel 1 goto :error
start "" http://127.0.0.1:8000
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 main.py
  goto :end
)
python main.py
goto :end
:error
echo TrafficScope could not be built.
pause
:end
