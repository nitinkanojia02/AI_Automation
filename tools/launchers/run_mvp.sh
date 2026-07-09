#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
AUTO_OPEN_BROWSER="${AUTO_OPEN_BROWSER:-0}"

cd "$ROOT_DIR"

echo "========================================"
echo " AI Automation MVP - One Click Runner"
echo "========================================"

echo "[1/5] Checking Python..."
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  echo "ERROR: Python executable '$PYTHON_BIN' was not found."
  echo "Set PYTHON_BIN or install Python 3."
  exit 1
fi

echo "Using Python: $(command -v "$PYTHON_BIN")"

if [ ! -d "$VENV_DIR" ]; then
  echo "[2/5] Creating virtual environment..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
else
  echo "[2/5] Virtual environment already exists."
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "[3/5] Installing Python dependencies..."
pip install --upgrade pip >/dev/null
pip install -r requirements.txt

echo "[4/5] Ensuring Playwright browser dependencies are installed..."
python -m playwright install chromium

if [ -z "${DEVEX_AI_TOKEN:-}" ]; then
  echo "WARNING: DEVEX_AI_TOKEN is not set."
  echo "AI-backed manual/automation generation may fail until you export it."
fi

URL="http://$HOST:$PORT"
echo "[5/5] Starting FastAPI app..."
echo "Open: $URL"
echo "Press Ctrl+C to stop."

if [ "$AUTO_OPEN_BROWSER" = "1" ]; then
  if command -v xdg-open >/dev/null 2>&1; then
    (sleep 3 && xdg-open "$URL" >/dev/null 2>&1 || true) &
  elif command -v open >/dev/null 2>&1; then
    (sleep 3 && open "$URL" >/dev/null 2>&1 || true) &
  fi
fi

exec python -m uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
