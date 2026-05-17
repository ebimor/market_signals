#!/bin/bash

# Run Portfolio Exposure Tests with proper environment setup
# Handles path and virtual environment automatically

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Set Python path to include project root
export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"

# Run the tests
python backend/risk/test_portfolio_exposure.py "$@"
