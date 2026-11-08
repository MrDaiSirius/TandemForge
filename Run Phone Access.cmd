@echo off
setlocal
set "TS=%ProgramFiles%\Tailscale\tailscale.exe"
if not exist "%TS%" set "TS=tailscale.exe"
powershell.exe -NoProfile -Command "try { Invoke-RestMethod 'http://127.0.0.1:8770/api/session' -TimeoutSec 2 -ErrorAction Stop | Out-Null; exit 0 } catch { exit 1 }"
if errorlevel 1 (
  echo Open TandemForge first.
  pause
  exit /b 1
)
"%TS%" serve --bg --https=8444 http://127.0.0.1:8770
if errorlevel 1 echo Sign in to Tailscale on Windows and your phone, then try again.
pause
