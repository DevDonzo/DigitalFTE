#!/bin/bash
echo "🛑 Stopping Digital FTE - All Services"
echo ""

# Kill all services from agents/ folder
pkill -f "agents/orchestrator"
pkill -f "agents/gmail_watcher"
pkill -f "agents/whatsapp_watcher"
pkill -f "agents/webhook_server"
pkill -f "agents/watchdog"

sleep 2
echo "✅ All services stopped!"
