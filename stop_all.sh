#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$ROOT_DIR/runtime"

echo "Stopping DigitalFTE services..."

if [ -f "$RUNTIME_DIR/pids" ]; then
  # shellcheck disable=SC1090
  source "$RUNTIME_DIR/pids"
  for pid in "${CONTROL_CENTER_PID:-}" "${LOCAL_ORCH_PID:-}" "${WEBHOOK_PID:-}" "${ORCHESTRATOR_PID:-}" "${GMAIL_PID:-}" "${WATCHDOG_PID:-}"; do
    if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
  done
fi

pkill -f "scripts/control_center.py" >/dev/null 2>&1 || true
pkill -f "agents/local_orchestrator.py" >/dev/null 2>&1 || true
pkill -f "scripts/orchestrator.py" >/dev/null 2>&1 || true
pkill -f "agents/orchestrator.py" >/dev/null 2>&1 || true
pkill -f "agents/gmail_watcher.py" >/dev/null 2>&1 || true
pkill -f "scripts/webhook_server.py" >/dev/null 2>&1 || true
pkill -f "agents/webhook_server.py" >/dev/null 2>&1 || true
pkill -f "scripts/watchdog.py" >/dev/null 2>&1 || true
pkill -f "agents/watchdog.py" >/dev/null 2>&1 || true

docker compose down >/dev/null 2>&1 || docker-compose down >/dev/null 2>&1 || true

rm -f "$RUNTIME_DIR/pids"
echo "All services stopped."
