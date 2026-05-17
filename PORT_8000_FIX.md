# Port 8000 Cleanup Scripts

## Problem
You get this error when starting the server:
```
ERROR:    [Errno 98] Address already in use
```

This happens when a previous server process didn't shut down cleanly.

## Solution

### Option 1: Automatic (Recommended)
Use `start-local.sh` - it automatically clears port 8000 before starting:
```bash
./start-local.sh
```

### Option 2: Quick Fix
If you just need to free up port 8000:
```bash
./fix-port-8000.sh
```

Then start the server separately:
```bash
cd backend
python -m uvicorn main:app --port 8000 --reload
```

### Option 3: Manual
Kill the process using port 8000:
```bash
# Find what's using port 8000
lsof -i :8000

# Kill it (replace PID with the actual process ID)
kill -9 <PID>

# Or force kill all Python processes on that port
pkill -f "python.*8000"
```

## How It Works

1. **fix-port-8000.sh** - Standalone script
   - Checks if port 8000 is in use
   - Gracefully terminates the process
   - Force kills if needed
   - Verifies port is free

2. **scripts/kill-port-8000.sh** - Helper script
   - Called automatically by start-local.sh
   - Cleans port before server starts
   - Waits up to 10 seconds for port to be available

## Troubleshooting

If port still shows as in use after running the script:
```bash
# List all processes using port 8000
lsof -i :8000

# Or use netstat (if lsof unavailable)
netstat -tuln | grep 8000
```

Then manually kill the persistent process or restart your terminal/system.
