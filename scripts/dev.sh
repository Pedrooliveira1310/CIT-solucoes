#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
.venv/bin/flask --app run cleanup-audio
.venv/bin/flask --app run cleanup-loop &
JANITOR_PID=$!
.venv/bin/python run.py &
SERVER_PID=$!
cleanup() {
  kill "$SERVER_PID" "$JANITOR_PID" 2>/dev/null || true
  wait "$SERVER_PID" "$JANITOR_PID" 2>/dev/null || true
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
wait "$SERVER_PID"
