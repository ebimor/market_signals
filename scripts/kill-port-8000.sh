#!/bin/bash

# Kill any process using port 8000 and wait for port to be available

PORT=8000
TIMEOUT=10
ELAPSED=0

# Check if port is in use and kill the process
PID=$(lsof -ti:$PORT 2>/dev/null)

if [ -n "$PID" ]; then
    echo "⚠️  Port $PORT is in use (PID: $PID)"
    echo "🧹 Killing process and cleaning up..."
    
    # Try graceful kill first
    kill -TERM $PID 2>/dev/null || true
    sleep 1
    
    # Force kill if still running
    kill -9 $PID 2>/dev/null || true
    
    # Wait for port to be released
    echo "⏳ Waiting for port $PORT to be available..."
    while [ $ELAPSED -lt $TIMEOUT ]; do
        if ! lsof -ti:$PORT >/dev/null 2>&1; then
            echo "✅ Port $PORT is now available"
            exit 0
        fi
        sleep 1
        ELAPSED=$((ELAPSED + 1))
    done
    
    echo "⚠️  Port $PORT still in use after ${TIMEOUT}s, attempting to continue..."
    exit 1
else
    echo "✅ Port $PORT is available"
    exit 0
fi
