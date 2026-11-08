@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -Command "try { Invoke-RestMethod 'http://127.0.0.1:8770/api/session' -TimeoutSec 2 -ErrorAction Stop | Out-Null; exit 0 } catch { exit 1 }"
if not errorlevel 1 (
  start "" "http://127.0.0.1:8770"
  echo Access code for the running app:
  if defined TANDEMFORGE_DATA (
    type "%TANDEMFORGE_DATA%\access-code.txt"
  ) else (
    type "%LOCALAPPDATA%\TandemForge\access-code.txt"
  )
  pause
  exit /b
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0bootstrap.ps1"
pause
