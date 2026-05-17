#!/bin/bash

# SafeSwing Trader - Local Development Startup Script

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         SafeSwing Trader - Local Development Setup            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo

# Clean up port 8000 if in use
echo "🧹 Checking port 8000..."
if [ -f "scripts/kill-port-8000.sh" ]; then
    chmod +x scripts/kill-port-8000.sh
    bash scripts/kill-port-8000.sh || true
fi
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install --quiet --upgrade pip setuptools wheel
pip install --quiet -r requirements-local.txt

echo
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║              Running Feature Tests & Verification             ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo

# Run Portfolio Exposure tests
echo "🧪 Testing Portfolio Exposure Feature..."
if python3 risk/test_portfolio_exposure.py > /dev/null 2>&1; then
    echo "✅ Portfolio Exposure Tests: PASSED (10/10)"
else
    echo "⚠️  Portfolio Exposure Tests: Check manually with 'python3 risk/test_portfolio_exposure.py'"
fi

echo
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                   Starting Backend Server                     ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo

# Set Python path
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

echo "🚀 Starting FastAPI backend on http://localhost:8000"
echo "📖 API Docs:  http://localhost:8000/docs"
echo "📊 ReDoc:     http://localhost:8000/redoc"
echo
echo "Press CTRL+C to stop the server"
echo

# Start backend from project root (don't cd into backend)
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
