#!/bin/bash
echo "🛑 Stopping Digital FTE - All Services"
echo ""

# Kill all services
pkill -f "scripts/orchestrator"
pkill -f "watchers/gmail_watcher"
pkill -f "watchers/whatsapp_watcher"
pkill -f "scripts/webhook_server"
pkill -f "scripts/watchdog"
pkill -f "scripts/weekly_audit"

sleep 2
echo "✅ All services stopped!"
