# Phase 4d: Quick Setup & Run Guide

## ⚡ 5-Minute Setup

### Prerequisites
- Node.js 18+ installed
- Backend running (Phase 4c API)

### Step 1: Install Frontend Dependencies (2 minutes)

```bash
cd frontend
npm install
```

### Step 2: Start Frontend Dev Server (1 minute)

```bash
npm run dev
```

Output will show:
```
  VITE v5.0.8  ready in 123 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h + enter to show help
```

### Step 3: Open Dashboard (30 seconds)

Visit: **http://localhost:5173**

You should see:
- SafeSwing Trader Dashboard header
- System status (green if API connected)
- 4 navigation tabs
- Empty states if no data from backend

---

## 🔗 Connect Backend

### Ensure Backend API is Running

```bash
# In a separate terminal
cd safeswing_trader
source venv/bin/activate
python -m uvicorn backend.main:app --reload
```

Backend should be on: **http://localhost:8000**

### Verify Connection

- Open browser DevTools (F12)
- Go to Network tab
- Click on Signals tab in dashboard
- Should see API calls to `/api/trading/*`
- Check for 200 status codes

---

## 🎮 Using the Dashboard

### 1. Signal Review (First Tab)
```
Create a signal in the API:
POST http://localhost:8000/api/trading/signals

Then in dashboard:
✓ See pending signals
✓ Modify position/SL/TP
✓ Click Approve or Reject
```

### 2. Open Positions (Second Tab)
```
After approving and executing trades:
✓ See active positions
✓ View entry/SL/TP
✓ Track distances
```

### 3. Trade History (Third Tab)
```
After closing trades:
✓ See all closed trades
✓ View P&L per trade
✓ Check win/loss status
```

### 4. Performance (Fourth Tab)
```
With multiple trades:
✓ See key metrics
✓ View win rate
✓ Check best/worst trades
✓ See total P&L
```

---

## 🐛 Troubleshooting

### "Cannot find module 'react'"
**Solution**: You haven't run `npm install`
```bash
npm install
```

### "http://localhost:5173 connection refused"
**Solution**: Dev server isn't running
```bash
npm run dev
```

### "API error" in dashboard
**Solution**: Backend not running
```bash
cd ../safeswing_trader
source venv/bin/activate
python -m uvicorn backend.main:app --reload
```

### "Port 5173 already in use"
**Solution**: Use different port
```bash
npm run dev -- --port 3000
```

### No data showing in dashboard
**Solution**: 
1. Check backend has test data
2. Look at browser console (F12)
3. Check Network tab for failed requests
4. Verify API URLs match

---

## 📦 Build for Production

```bash
npm run build
```

Creates optimized build in `dist/` folder.

To preview production build:
```bash
npm run preview
```

---

## 📁 Project Files

Essential files to know:

| File | Purpose |
|------|---------|
| `src/App.tsx` | Main app component |
| `src/hooks/useTrading.ts` | API data & actions |
| `src/services/api.ts` | Backend API client |
| `src/components/*.tsx` | UI components |
| `src/styles/*.css` | Component styling |
| `vite.config.ts` | Build config |
| `package.json` | Dependencies |

---

## 🔧 Configuration

### Change API URL

Edit `src/services/api.ts`:
```typescript
const API_BASE = 'http://localhost:8000/api/trading';
```

### Change Frontend Port

Edit `vite.config.ts`:
```typescript
server: {
  port: 5173,  // Change this
}
```

### Change Polling Interval

Edit `src/hooks/useTrading.ts`:
```typescript
const interval = setInterval(refreshAll, 5000);  // milliseconds
```

---

## ✅ Quick Checklist

- [ ] `npm install` completed
- [ ] `npm run dev` started
- [ ] Browser opened to http://localhost:5173
- [ ] Dashboard visible
- [ ] Backend running on port 8000
- [ ] No console errors
- [ ] System status shows "Running"

---

## 🚀 Next Steps

1. **Test with Mock Data**
   - Use example_trading_api.py to create test signals
   - See them appear in dashboard

2. **Test Real Workflow**
   - Create signal → Approve → Execute → Close
   - Watch all tabs update in real-time

3. **Try All Tabs**
   - Signals: Approve/reject/modify
   - Positions: View active trades
   - History: See closed trades
   - Performance: View analytics

4. **Connect Mobile** (Optional)
   - Change localhost to machine IP in vite.config.ts
   - Access from phone on same network

---

## 📊 What You Should See

### Signals Tab
```
Pending Signals (2)

[AAPL BUY] 
Entry: $150.25  SL: $148  TP: $155  Conf: 75%
Position: [100] Stop: [148] TP: [155]
[Approve] [Reject]

[TSLA BUY]
Entry: $850  SL: $820  TP: $900  Conf: 65%
Position: [150] Stop: [820] TP: [900]
[Approve] [Reject]
```

### Performance Tab
```
Key Metrics:
Total Trades: 5        Win Rate: 60%
Total P&L: $1,234.50   Avg P&L: $246.90
Best Trade: $567.00    Worst Trade: -$145.00

[Charts showing win/loss distribution and metrics]
```

### Trade History Tab
```
Symbol | Entry    | Exit     | Position | P&L      | Return
AAPL   | $150.25  | $155.00  | 100      | +$475.00 | +3.16%
TSLA   | $850.00  | $825.00  | 150      | -$165.00 | -2.20%
```

---

## 🎯 Success Criteria

- [x] Frontend loads without errors
- [x] All 4 tabs accessible
- [x] System status shows connected
- [x] Can see pending signals (if any)
- [x] Can approve/reject signals
- [x] Trade history shows closed trades
- [x] Performance metrics display
- [x] Charts render
- [x] Auto-refresh every 5 seconds
- [x] Responsive on mobile

---

**Phase 4d Ready to Go! 🚀**

Start with: `npm run dev`
