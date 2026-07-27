#!/bin/bash
set -e

echo "🚀 Deploying AI Finance Tracker Bot (no Docker)..."

cd "$(dirname "$0")"

# Stop any existing bot process
echo "🛑 Stopping any existing bot process..."
pkill -f "python3 main.py" 2>/dev/null || true
pkill -f "python main.py" 2>/dev/null || true
sleep 1

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt --quiet

# Create necessary directories
mkdir -p downloads/receipts

# Create database file if not exists
touch finance_bot.db

# Start bot in background
echo "▶️ Starting bot in background..."
nohup python3 main.py > bot.log 2>&1 &
BOT_PID=$!

sleep 2

# Check if started successfully
if kill -0 $BOT_PID 2>/dev/null; then
    echo "✅ Bot successfully started! PID: $BOT_PID"
    echo "📋 View logs: tail -f bot.log"
    echo "🛑 Stop bot: pkill -f 'python3 main.py'"
else
    echo "❌ Bot failed to start! Check logs:"
    cat bot.log
    exit 1
fi
