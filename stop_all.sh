#!/bin/bash
echo "🛑 Stopping Digital FTE - All Services"
echo ""

# Kill all services
pkill -f "scripts/orchestrator"
pkill -f "watchers/gmail_watcher"
pkill -f "watchers/whatsapp_watcher"
pkill -f "watchers/linkedin_watcher"
pkill -f "scripts/webhook_server"
pkill -f "scripts/watchdog"

sleep 2
echo "✅ All services stopped!"
