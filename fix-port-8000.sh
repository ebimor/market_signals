#!/bin/bash

# Quick fix for "Address already in use" error on port 8000
# Usage: ./fix-port-8000.sh

echo "🔧 SafeSwing Trader - Port 8000 Quick Fix"
echo ""

PORT=8000

# Check if lsof is available
if ! command -v lsof &> /dev/null; then
    echo "⚠️  lsof not found. Using alternative method..."
    netstat -tuln | grep ":$PORT " > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "❌ Port $PORT is still in use"
        echo "📝 Try running: sudo lsof -ti:8000 | xargs kill -9"
        exit 1
    else
        echo "✅ Port $PORT is available"
        exit 0
    fi
fi

# Get process using port
PID=$(lsof -ti:$PORT 2>/dev/null)

if [ -z "$PID" ]; then
    echo "✅ Port $PORT is already available"
    exit 0
fi

echo "❌ Port $PORT is in use"
echo "   Process ID: $PID"
echo ""

# Try to get process info
PROCESS=$(lsof -i :$PORT 2>/dev/null | tail -1)
echo "   Process: $PROCESS"
echo ""

# Kill the process
echo "🧹 Killing process..."
kill -TERM $PID 2>/dev/null && sleep 1 || true

# Check if still running
if kill -0 $PID 2>/dev/null; then
    echo "⚠️  Process still running, forcing kill..."
    kill -9 $PID
fi

sleep 1

# Verify port is free
if lsof -ti:$PORT >/dev/null 2>&1; then
    echo "❌ Port $PORT still in use"
    exit 1
else
    echo "✅ Port $PORT is now available"
    exit 0
fi
