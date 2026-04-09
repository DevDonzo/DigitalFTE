#!/usr/bin/env bash
# Launch the local DigitalFTE operating stack.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$ROOT_DIR/runtime"
PORT="${CONTROL_CENTER_PORT:-8282}"
WEBHOOK_PORT="${WEBHOOK_PORT:-8001}"

mkdir -p "$RUNTIME_DIR"
cd "$ROOT_DIR"

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

echo "DigitalFTE"
echo "=========="
echo "Workspace: $ROOT_DIR"
echo ""

if command -v docker >/dev/null 2>&1; then
  echo "Bringing up Odoo stack..."
  docker compose up -d >/dev/null 2>&1 || docker-compose up -d >/dev/null 2>&1 || true
else
  echo "Docker not found; skipping Odoo startup."
fi

echo "Starting control center on http://127.0.0.1:$PORT ..."
nohup python3 scripts/control_center.py >"$RUNTIME_DIR/control_center.log" 2>&1 &
CONTROL_CENTER_PID=$!

echo "Starting local orchestrator ..."
nohup python3 agents/local_orchestrator.py >"$RUNTIME_DIR/local_orchestrator.log" 2>&1 &
LOCAL_ORCH_PID=$!

if [ -n "${TWILIO_ACCOUNT_SID:-}" ] && [ -n "${TWILIO_AUTH_TOKEN:-}" ]; then
  echo "Starting WhatsApp webhook on http://127.0.0.1:$WEBHOOK_PORT ..."
  nohup python3 scripts/webhook_server.py >"$RUNTIME_DIR/webhook.log" 2>&1 &
  WEBHOOK_PID=$!
else
  WEBHOOK_PID=""
  echo "Twilio credentials not configured; webhook server not started."
fi

if [ -n "${GMAIL_CLIENT_ID:-}" ] && [ -n "${GMAIL_CLIENT_SECRET:-}" ]; then
  echo "Starting full orchestrator ..."
  nohup python3 scripts/orchestrator.py >"$RUNTIME_DIR/orchestrator.log" 2>&1 &
  ORCHESTRATOR_PID=$!

  echo "Starting Gmail watcher ..."
  nohup python3 agents/gmail_watcher.py >"$RUNTIME_DIR/gmail_watcher.log" 2>&1 &
  GMAIL_PID=$!

  echo "Starting watchdog ..."
  nohup python3 scripts/watchdog.py >"$RUNTIME_DIR/watchdog.log" 2>&1 &
  WATCHDOG_PID=$!
else
  ORCHESTRATOR_PID=""
  GMAIL_PID=""
  WATCHDOG_PID=""
  echo "Gmail credentials not configured; automation watchers remain off."
fi

cat >"$RUNTIME_DIR/pids" <<EOF
CONTROL_CENTER_PID=$CONTROL_CENTER_PID
LOCAL_ORCH_PID=$LOCAL_ORCH_PID
WEBHOOK_PID=$WEBHOOK_PID
ORCHESTRATOR_PID=$ORCHESTRATOR_PID
GMAIL_PID=$GMAIL_PID
WATCHDOG_PID=$WATCHDOG_PID
EOF

echo ""
echo "Live surfaces"
echo "-------------"
echo "Control Center: http://127.0.0.1:$PORT"
echo "Vault Dashboard: vault/Dashboard.md"
echo "Briefings: vault/Briefings/"
echo ""
echo "Logs"
echo "----"
echo "tail -f runtime/control_center.log"
echo "tail -f runtime/local_orchestrator.log"
echo ""
echo "Stop"
echo "----"
echo "./stop_all.sh"
