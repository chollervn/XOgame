@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD="
if exist ".venv\Scripts\python.exe" (
  set "PYTHON_CMD=.venv\Scripts\python.exe"
) else (
  where py >nul 2>&1
  if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
  ) else (
    set "PYTHON_CMD=python"
  )
)

echo Using %PYTHON_CMD%

call %PYTHON_CMD% -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
  echo Installing dependencies...
  call %PYTHON_CMD% -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
  )
)

call %PYTHON_CMD% run_game.py
if errorlevel 1 (
  echo Game stopped because of an error.
  pause
  exit /b 1
)

endlocal
