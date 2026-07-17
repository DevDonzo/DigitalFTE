#!/usr/bin/env bash
# Launch the local DigitalFTE operating stack.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNTIME_DIR="$ROOT_DIR/runtime"
PORT="${CONTROL_CENTER_PORT:-8282}"
WEBHOOK_PORT="${WEBHOOK_PORT:-8001}"

mkdir -p "$RUNTIME_DIR"
cd "$ROOT_DIR"

env_has() {
  python3 - "$1" <<'PY'
import os
import sys
from pathlib import Path

key = sys.argv[1]

def usable(value):
    if not value:
        return False
    normalized = value.strip().strip("'\"").lower()
    placeholders = ("your_", "example", "changeme", "replace-me", "replace_me", "todo")
    return bool(normalized) and not any(fragment in normalized for fragment in placeholders)

if usable(os.getenv(key)):
    raise SystemExit(0)

env_path = Path(".env")
if not env_path.exists():
    raise SystemExit(1)

for line in env_path.read_text(encoding="utf-8").splitlines():
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or "=" not in stripped:
        continue
    name, value = stripped.split("=", 1)
    if name.strip() == key and usable(value):
        raise SystemExit(0)

raise SystemExit(1)
PY
}

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source ".venv/bin/activate"
fi

if [ -f "$RUNTIME_DIR/pids" ]; then
  while IFS='=' read -r pid_name service_pid; do
    case "$pid_name" in
      CONTROL_CENTER_PID|WEBHOOK_PID|ORCHESTRATOR_PID|GMAIL_PID)
        if [[ "$service_pid" =~ ^[0-9]+$ ]] && kill -0 "$service_pid" >/dev/null 2>&1; then
          echo "DigitalFTE is already running (PID $service_pid). Run ./stop_all.sh first."
          exit 1
        fi
        ;;
    esac
  done < "$RUNTIME_DIR/pids"
fi

RUNTIME_PORTS="$(python3 - <<'PY'
from utils.config_loader import load_config

config = load_config()
print(f"{config['CONTROL_CENTER_PORT']}:{config['WEBHOOK_PORT']}")
PY
)"
PORT="${RUNTIME_PORTS%%:*}"
WEBHOOK_PORT="${RUNTIME_PORTS##*:}"

python3 - <<'PY'
from utils.config_loader import load_config

vault = load_config()["VAULT_PATH"]
for folder in (
    "Inbox",
    "Needs_Action",
    "Plans",
    "Pending_Approval",
    "Approved",
    "Rejected",
    "Failed",
    "Done",
    "Logs",
    "Briefings",
    "Agent_Transcripts",
):
    (vault / folder).mkdir(parents=True, exist_ok=True)
print(f"Vault: {vault}")
PY

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

echo "Starting orchestrator ..."
nohup python3 scripts/orchestrator.py >"$RUNTIME_DIR/orchestrator.log" 2>&1 &
ORCHESTRATOR_PID=$!

if (env_has TWILIO_ACCOUNT_SID && env_has TWILIO_AUTH_TOKEN) || \
   (env_has META_APP_SECRET && env_has WHATSAPP_WEBHOOK_VERIFY_TOKEN); then
  echo "Starting WhatsApp webhook on http://127.0.0.1:$WEBHOOK_PORT ..."
  nohup python3 scripts/webhook_server.py >"$RUNTIME_DIR/webhook.log" 2>&1 &
  WEBHOOK_PID=$!
else
  WEBHOOK_PID=""
  echo "Twilio credentials not configured; webhook server not started."
fi

if env_has GMAIL_CLIENT_ID && env_has GMAIL_CLIENT_SECRET; then
  echo "Starting Gmail watcher ..."
  nohup python3 agents/gmail_watcher.py >"$RUNTIME_DIR/gmail_watcher.log" 2>&1 &
  GMAIL_PID=$!
else
  GMAIL_PID=""
  echo "Gmail credentials not configured; Gmail watcher not started."
fi

cat >"$RUNTIME_DIR/pids" <<EOF
CONTROL_CENTER_PID=$CONTROL_CENTER_PID
WEBHOOK_PID=$WEBHOOK_PID
ORCHESTRATOR_PID=$ORCHESTRATOR_PID
GMAIL_PID=$GMAIL_PID
EOF

echo ""
echo "Live surfaces"
echo "-------------"
echo "Control Center: http://127.0.0.1:$PORT"
echo "Vault Dashboard: ./vault/Dashboard.md"
echo ""
echo "Logs"
echo "----"
echo "tail -f runtime/control_center.log"
echo "tail -f runtime/orchestrator.log"
echo ""
echo "Stop"
echo "----"
echo "./stop_all.sh"
