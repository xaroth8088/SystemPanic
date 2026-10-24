@echo off
setlocal
cd /d "%~dp0"
if not exist .asset-tools\audio-env\Scripts\python.exe (
  py -3.12 tools\assetforge\local.py install
  if errorlevel 1 goto fail
)
.asset-tools\audio-env\Scripts\python.exe -c "import gradio, ai_edge_litert" >nul 2>&1
if errorlevel 1 (
  py -3.12 tools\assetforge\local.py install
  if errorlevel 1 goto fail
)
echo Local Audio Studio: http://127.0.0.1:7871
.asset-tools\audio-env\Scripts\python.exe tools\assetforge\local.py serve
if errorlevel 1 goto fail
exit /b 0
:fail
echo Audio Studio could not start. See the error above.
pause
exit /b 1
