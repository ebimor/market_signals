#!/bin/bash

# SafeSwing Trader - Simple Launch Script

# Get the script directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║          SafeSwing Trader - Unified Startup Script          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"

# 1. Kill any existing processes
echo -e "${YELLOW}🧹 Cleaning up existing processes...${NC}"
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3001 | xargs kill -9 2>/dev/null || true

# 2. Setup Backend Environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
fi

source venv/bin/activate
echo -e "${GREEN}✅ Backend environment ready.${NC}"

# 3. Start Backend in background
echo -e "${YELLOW}🚀 Starting Backend Server (Port 8000)...${NC}"
export PYTHONPATH="$PROJECT_DIR"
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 > /tmp/safeswing_backend.log 2>&1 &
BACKEND_PID=$!

# 4. Start Frontend in background
echo -e "${YELLOW}🌐 Starting Frontend Interface (Port 3001)...${NC}"
cd "$PROJECT_DIR/frontend"
# We force the port to 3001 as requested
npm run dev -- --port 3001 > /tmp/safeswing_frontend.log 2>&1 &
FRONTEND_PID=$!

echo -e "${GREEN}═════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🚀 Application is launching!${NC}"
echo -e "${BLUE}📊 Frontend Dashboard: ${NC} http://localhost:3001"
echo -e "${BLUE}📖 Backend API Docs:  ${NC} http://localhost:8000/docs"
echo -e "${YELLOW}═════════════════════════════════════════════════════════════════${NC}"
echo "Logs are available at:"
echo " - /tmp/safeswing_backend.log"
echo " - /tmp/safeswing_frontend.log"
echo -e "${YELLOW}Press Ctrl+C to stop both servers.${NC}"

# Handle Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; echo -e '\n${YELLOW}Stopping servers...${NC}'; exit" INT

# Wait for background processes
wait
