# 🚀 SafeSwing Trader - System Launch Guide

**Phase 4d Complete - Ready to Deploy**

---

## ⚡ Quick Start (2 Minutes)

### Option 1: One-Command Launch (Easiest)

```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader

# Terminal 1: Start Backend
/home/eshahrivar/test_hedge_ai/safeswing_trader/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Start Frontend
cd frontend && npm run dev
```

Then visit: **http://localhost:3000**

---

## 📋 Step-by-Step Launch

### **Step 1: Open Terminal 1 (Backend)**

```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader
```

### **Step 2: Activate Virtual Environment (Backend)**

```bash
source venv/bin/activate
```

Or use full path:
```bash
. /home/eshahrivar/test_hedge_ai/safeswing_trader/venv/bin/activate
```

### **Step 3: Start Backend API Server**

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
INFO:     Uvicorn running with auto reload enabled
```

### **Step 4: Open Terminal 2 (Frontend)**

In a **NEW terminal window**, run:

```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader/frontend
```

### **Step 5: Start Frontend Dev Server**

```bash
npm run dev
```

**Expected Output:**
```
  VITE v5.4.21  ready in 130 ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
```

### **Step 6: Open Dashboard in Browser**

Visit: **http://localhost:3000**

---

## ✅ Verify Both Servers Are Running

### Check Backend (Port 8000)

```bash
# Test 1: Check process
ps aux | grep uvicorn | grep -v grep

# Test 2: Test API endpoint
curl -s http://localhost:8000/api/trading/status | python3 -m json.tool
```

**Expected Response:**
```json
{
    "status": "running",
    "pending_signals": 0,
    "open_trades": 0,
    "closed_trades": 0,
    "total_trades": 0,
    "timestamp": "2026-05-17T15:42:40.510124"
}
```

### Check Frontend (Port 3000)

```bash
# Test 1: Check process
ps aux | grep vite | grep -v grep

# Test 2: Check if page loads
curl -s http://localhost:3000 | head -c 200
```

---

## 🎯 What You'll See

### Dashboard Tabs
1. **Signals** - Pending trade signals for approval
2. **Trade History** - All closed trades with P&L
3. **Performance** - Charts and key metrics
4. **Positions** - Active open trades
5. **Status** - System health in header

### Features
- ✅ Real-time data updates (every 5 seconds)
- ✅ Color-coded P&L (green = profit, red = loss)
- ✅ Professional charts (Recharts visualizations)
- ✅ Responsive design (works on mobile)
- ✅ Manual approval workflow (approve/reject signals)

---

## 🔧 Alternative Launch Methods

### Using Full Paths (No Virtual Env)

**Backend:**
```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader
/home/eshahrivar/test_hedge_ai/safeswing_trader/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader/frontend
npm run dev
```

### Background Launch (Detached)

**Backend (in background):**
```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader
/home/eshahrivar/test_hedge_ai/safeswing_trader/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
```

**Frontend (in background):**
```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader/frontend
npm run dev > /tmp/frontend.log 2>&1 &
```

Check logs:
```bash
tail -f /tmp/backend.log
tail -f /tmp/frontend.log
```

---

## 🛑 Stopping the System

### Stop Backend
```bash
# Method 1: Ctrl+C in terminal where it's running

# Method 2: Kill the process
pkill -f "uvicorn.*backend.main"

# Method 3: Kill by port
lsof -ti:8000 | xargs kill -9
```

### Stop Frontend
```bash
# Method 1: Ctrl+C in terminal where it's running

# Method 2: Kill the process
pkill -f vite

# Method 3: Kill by port
lsof -ti:3000 | xargs kill -9
```

### Stop All

```bash
pkill -f "uvicorn.*backend.main"
pkill -f vite
```

---

## 🔄 Restart the System

### Quick Restart Script

Create file: `restart.sh`

```bash
#!/bin/bash

# Kill existing processes
pkill -f "uvicorn.*backend.main"
pkill -f vite
sleep 2

# Start backend
cd /home/eshahrivar/test_hedge_ai/safeswing_trader
/home/eshahrivar/test_hedge_ai/safeswing_trader/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &

# Start frontend
cd frontend
npm run dev > /tmp/frontend.log 2>&1 &

echo "✅ System restarted"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
```

Run it:
```bash
chmod +x restart.sh
./restart.sh
```

---

## 📊 System Architecture

```
User Browser
    ↓
http://localhost:3000
    ↓
React Dashboard (Vite Dev Server)
    ↓ (Axios HTTP Requests)
    ↓
http://localhost:8000/api/*
    ↓
FastAPI Backend (Uvicorn)
    ↓
SQLite Database + Signal Generator + Risk Engine
```

---

## 📁 Directory Structure

```
/home/eshahrivar/test_hedge_ai/safeswing_trader/
├── backend/                 # Python FastAPI backend
│   ├── main.py             # FastAPI app entry point
│   ├── api/                # API routes
│   ├── signals/            # Signal generation
│   ├── risk/               # Risk management
│   ├── data/               # Data storage (SQLite, JSON)
│   └── ...
├── frontend/               # React dashboard
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── styles/
│   ├── package.json
│   ├── vite.config.ts
│   └── ...
├── venv/                   # Python virtual environment
└── ...
```

---

## 🌐 API Endpoints

Once backend is running, access:

**API Documentation:**
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)

**Key Endpoints:**
- `GET /api/trading/status` - System status
- `GET /api/trading/signals` - Pending signals
- `POST /api/trading/approve` - Approve signal
- `GET /api/trading/trades/open` - Open trades
- `GET /api/trading/trades/history` - Trade history
- `GET /api/trading/stats` - Performance stats

---

## 🧪 Test the Connection

### Option 1: Using Browser

1. Visit: **http://localhost:3000**
2. Should see React dashboard
3. Open DevTools (F12) → Network tab
4. Should see requests to http://localhost:8000

### Option 2: Using curl

```bash
# Test backend API
curl -s http://localhost:8000/api/trading/status | python3 -m json.tool

# Test frontend  
curl -s http://localhost:3000 | head -c 300
```

### Option 3: Check Logs

**Backend:**
```bash
tail -20 /tmp/backend.log
```

**Frontend:**
```bash
tail -20 /tmp/frontend.log
```

---

## ⚠️ Troubleshooting

### Port Already in Use

```bash
# Find what's using port 8000
lsof -i :8000

# Find what's using port 3000
lsof -i :3000

# Kill processes
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### Virtual Environment Not Found

```bash
# Check venv exists
ls -la /home/eshahrivar/test_hedge_ai/safeswing_trader/venv/bin/python

# Use full path to Python
/home/eshahrivar/test_hedge_ai/safeswing_trader/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### npm Dependencies Missing

```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader/frontend
npm install
```

### API Connection Error

1. Check backend is running: `ps aux | grep uvicorn | grep -v grep`
2. Test endpoint: `curl http://localhost:8000/api/trading/status`
3. Check logs: `tail -50 /tmp/backend.log`

---

## 🎯 Typical Workflow

### 1. First-Time Setup

```bash
# Just one time:
cd /home/eshahrivar/test_hedge_ai/safeswing_trader/frontend
npm install
```

### 2. Daily Launch (Both Terminals)

**Terminal 1:**
```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader
source venv/bin/activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2:**
```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader/frontend
npm run dev
```

### 3. Open Dashboard

Visit: **http://localhost:3000**

### 4. Use Dashboard

- Review signals in "Signals" tab
- Approve/reject signals
- View open trades in "Positions" tab
- Check performance in "Performance" tab

---

## 📱 Access from Other Machines

To access dashboard from another machine on your network:

1. Find your machine IP: `hostname -I`
2. Replace `localhost` with your IP
3. Example: `http://192.168.1.100:3000`

**Backend:**
```bash
# Start with 0.0.0.0 to allow external access
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
# Update vite.config.ts if needed
```

---

## 🚀 Production Deployment

### Build Frontend for Production

```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader/frontend
npm run build
```

Creates: `dist/` folder with optimized build

### Run Backend in Production

```bash
# Without auto-reload
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker (Optional)

```bash
# Backend only
docker build -f Dockerfile.backend -t safeswing-backend .
docker run -p 8000:8000 safeswing-backend

# Frontend
docker build -f Dockerfile.frontend -t safeswing-frontend .
docker run -p 3000:3000 safeswing-frontend
```

---

## ✨ System Status Checklist

| Component | Check Command | Expected Result |
|-----------|---------------|-----------------|
| Backend Running | `ps aux \| grep uvicorn` | Python process with backend.main |
| Backend Port | `lsof -i :8000` | Shows python on port 8000 |
| Backend API | `curl http://localhost:8000/api/trading/status` | JSON response with status |
| Frontend Running | `ps aux \| grep vite` | Node process with vite |
| Frontend Port | `lsof -i :3000` | Shows node on port 3000 |
| Frontend Loading | `curl http://localhost:3000` | HTML page content |

---

## 🎓 Next Steps After Launch

1. ✅ **Verify Dashboard Loads** - Check all tabs render
2. ✅ **Test API Connection** - Confirm data displays
3. ✅ **Create Test Signals** - Generate sample data
4. ✅ **Test Signal Approval** - Approve/reject workflow
5. ✅ **View Performance** - Check metrics display
6. ✅ **Monitor Auto-Refresh** - Verify 5-second updates

---

## 📞 Emergency Commands

```bash
# Kill everything and restart
pkill -9 -f "uvicorn\|vite\|npm"; sleep 2; \
cd /home/eshahrivar/test_hedge_ai/safeswing_trader && \
/home/eshahrivar/test_hedge_ai/safeswing_trader/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 & \
cd frontend && npm run dev > /tmp/frontend.log 2>&1 &
```

---

## ✅ Launch Checklist

- [ ] Open 2 terminals
- [ ] Navigate to correct directories
- [ ] Activate virtual environment (backend)
- [ ] Start backend on port 8000
- [ ] Verify backend is running
- [ ] Start frontend on port 3000
- [ ] Verify frontend is running
- [ ] Open http://localhost:3000 in browser
- [ ] See dashboard load
- [ ] Check all tabs are clickable
- [ ] Verify system status shows green
- [ ] Ready to test!

---

## 🎉 You're Ready!

The SafeSwing Trader system is fully functional and ready to use.

**Quick Launch Command:**

```bash
# Terminal 1
cd /home/eshahrivar/test_hedge_ai/safeswing_trader && source venv/bin/activate && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2
cd /home/eshahrivar/test_hedge_ai/safeswing_trader/frontend && npm run dev

# Then open: http://localhost:3000
```

**Happy Trading! 🚀**

---

**Last Updated**: May 17, 2026  
**System**: SafeSwing Trader Phase 4d  
**Status**: ✅ Ready to Launch
