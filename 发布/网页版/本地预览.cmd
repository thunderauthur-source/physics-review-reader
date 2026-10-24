@echo off
setlocal
cd /d "%~dp0"
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo Python not found.
  echo Upload this folder to a static host, or install Python 3.
  pause
  exit /b 1
)
start "Physics Reader Preview" cmd /k "%PY% -m http.server 8080 --bind 127.0.0.1"
timeout /t 2 >nul
start "" "http://127.0.0.1:8080/"
exit /b 0
