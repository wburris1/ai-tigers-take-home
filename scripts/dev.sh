#!/usr/bin/env bash
# One-shot local setup: Python venv + deps, npm install, then API + Vite dev servers.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VENV="$ROOT/.venv"
PY="$VENV/bin/python"
PIP="$VENV/bin/pip"

if [[ ! -x "$PY" ]]; then
  echo "Creating virtual environment at .venv ..."
  python3 -m venv "$VENV"
fi

echo "Installing Python dependencies ..."
"$PIP" install -r "$ROOT/api/requirements.txt"

echo "Installing npm dependencies ..."
npm install

cleanup() {
  if [[ -n "${UVICORN_PID:-}" ]] && kill -0 "$UVICORN_PID" 2>/dev/null; then
    kill "$UVICORN_PID" 2>/dev/null || true
    wait "$UVICORN_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "Starting API at http://127.0.0.1:8000 ..."
(cd "$ROOT/api" && "$PY" -m uvicorn main:app --reload --host 127.0.0.1 --port 8000) &
UVICORN_PID=$!

echo "Starting frontend at http://127.0.0.1:3000 ..."
npm run dev
