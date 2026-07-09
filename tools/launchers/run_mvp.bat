@echo off
setlocal

set "ROOT_DIR=%~dp0\..\.."
pushd "%ROOT_DIR%"

if "%PYTHON_BIN%"=="" set "PYTHON_BIN=python"
if "%HOST%"=="" set "HOST=127.0.0.1"
if "%PORT%"=="" set "PORT=8000"
if "%AUTO_OPEN_BROWSER%"=="" set "AUTO_OPEN_BROWSER=0"

echo ========================================
echo  AI Automation MVP - One Click Runner
echo ========================================

echo [1/5] Checking Python...
where %PYTHON_BIN% >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python executable '%PYTHON_BIN%' was not found.
  echo Set PYTHON_BIN or install Python 3.
  popd
  exit /b 1
)

echo [2/5] Creating virtual environment if needed...
if not exist ".venv\Scripts\python.exe" (
  %PYTHON_BIN% -m venv .venv
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo ERROR: Failed to activate virtual environment.
  popd
  exit /b 1
)

echo [3/5] Installing Python dependencies...
python -m pip install --upgrade pip >nul
pip install -r requirements.txt
if errorlevel 1 (
  echo ERROR: Dependency installation failed.
  popd
  exit /b 1
)

echo [4/5] Ensuring Playwright browser dependencies are installed...
python -m playwright install chromium
if errorlevel 1 (
  echo ERROR: Playwright Chromium installation failed.
  popd
  exit /b 1
)

if "%DEVEX_AI_TOKEN%"=="" (
  echo WARNING: DEVEX_AI_TOKEN is not set.
  echo AI-backed manual/automation generation may fail until you set it.
)

set "URL=http://%HOST%:%PORT%"
echo [5/5] Starting FastAPI app...
echo Open: %URL%
echo Press Ctrl+C to stop.

if "%AUTO_OPEN_BROWSER%"=="1" start "" %URL%

python -m uvicorn app.main:app --host %HOST% --port %PORT% --reload
set "EXIT_CODE=%ERRORLEVEL%"

popd
exit /b %EXIT_CODE%
