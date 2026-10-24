@echo off
copy "%~dp0*.lnk" "%USERPROFILE%\Desktop\" >nul
if errorlevel 1 (echo Copy failed. & pause) else (echo Shortcut copied to Desktop. & timeout /t 2 >nul)
