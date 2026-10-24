@echo off
cd /d "%~dp0"
QMLauncher.exe
if errorlevel 1 (
  echo Launcher failed. See launcher-error.log.
  pause
)
