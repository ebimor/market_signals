#!/bin/bash
# Quick start script for SafeSwing Trader backend

set -e

echo "SafeSwing Trader - Backend Quick Start"
echo "======================================"

# Check Python version
echo "Checking Python version..."
python --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Copy .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

# Initialize database
echo "Initializing database..."
python -c "from database.db import init_db; init_db()"

# Run tests
echo ""
echo "Running market data collector tests..."
echo "======================================"
python test_market_data.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the server, run:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
echo "To access API documentation:"
echo "  http://localhost:8000/docs"
echo ""
