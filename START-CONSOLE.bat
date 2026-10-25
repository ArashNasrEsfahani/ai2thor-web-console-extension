@echo off
rem Windows launcher: runs scripts/start_console.sh inside WSL2 and opens the console in your browser.
rem   START-CONSOLE.bat                 planner on (Ollama running on Windows with OLLAMA_HOST=0.0.0.0)
rem   START-CONSOLE.bat --no-llm        drive the simulator by hand only
rem Settings: WSLDISTRO (default Ubuntu-22.04) and THOR_PYTHON (default ~/thor-env/bin/python inside WSL).
setlocal
if "%WSLDISTRO%"=="" set "WSLDISTRO=Ubuntu-22.04"
if "%THOR_PYTHON%"=="" set "THOR_PYTHON=~/thor-env/bin/python"
set "REPO=%~dp0"
if "%REPO:~-1%"=="\" set "REPO=%REPO:~0,-1%"
for /f "delims=" %%p in ('wsl -d %WSLDISTRO% wslpath -a "%REPO%"') do set "WREPO=%%p"
if "%WREPO%"=="" (
  echo Could not reach the WSL distro "%WSLDISTRO%". Check:  wsl --list --verbose
  exit /b 1
)
echo Repository in WSL: %WREPO%
start "AI2-THOR web console - close this window to stop it" wsl -d %WSLDISTRO% --cd "%WREPO%" -- bash -lc "PYTHON=%THOR_PYTHON% scripts/start_console.sh %*"
echo Waiting for the console on http://localhost:8000 ...
for /l %%i in (1,1,90) do (
  powershell -NoProfile -Command "try{(Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://localhost:8000/status) | Out-Null; exit 0}catch{exit 1}" >nul 2>nul && goto OPEN
  timeout /t 2 /nobreak >nul
)
echo The console did not answer within 3 minutes; look at the console window for the error.
exit /b 1
:OPEN
start "" http://localhost:8000
echo Console is up: http://localhost:8000
