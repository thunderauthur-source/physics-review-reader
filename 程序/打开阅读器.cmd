@echo off
cd /d "%~dp0"
if exist "物理复习提纲阅读器.lnk" (
  start "" "物理复习提纲阅读器.lnk"
) else (
  start "" "阅读器.html"
)
