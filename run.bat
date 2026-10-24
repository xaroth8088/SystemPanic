@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  py -3.12 -m venv .venv
  if errorlevel 1 goto fail
)
.venv\Scripts\python.exe -c "import pygame; assert pygame.version.ver == '2.6.1'" >nul 2>&1
if errorlevel 1 (
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto fail
)
.venv\Scripts\python.exe play.py %*
if errorlevel 1 goto fail
exit /b 0
:fail
echo System Panic could not start. See the error above.
pause
exit /b 1
