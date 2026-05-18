#!/bin/bash

# SafeSwing Trader - Unified local quality checks
# Runs backend tests + frontend type checks (+ optional lint)

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "=========================================="
echo "SafeSwing Trader - Local CI Checks"
echo "=========================================="

cd "$PROJECT_DIR"

if [ ! -d "venv" ]; then
  echo "❌ Missing virtual environment at ./venv"
  echo "Create it first: python3 -m venv venv"
  exit 1
fi

echo
echo "[1/3] Backend tests"
. ./venv/bin/activate
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests


echo
echo "[2/3] Frontend type check"
cd "$PROJECT_DIR/frontend"
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi
node_modules/.bin/tsc --noEmit


echo
echo "[3/3] Frontend lint (optional)"
if [ -x "node_modules/.bin/eslint" ]; then
  npm run lint
else
  echo "⚠️  eslint not installed; skipping lint"
fi

echo
echo "✅ All checks completed successfully"
