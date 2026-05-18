# How to Test RSI Code - Quick Guide

## 4 Ways to Test

### 1️⃣ RUN THE AUTOMATED TEST SUITE (Quickest)

```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader
source venv/bin/activate
python backend/signals/test_rsi.py
```

**Output:**
- ✅ Test 1: Basic RSI calculation
- ✅ Test 2: Real market data (with yfinance if available)
- ✅ Test 3: Signal generation (BUY/SELL/HOLD)
- ✅ Test 4: Error handling (insufficient data)

---

### 2️⃣ TEST VIA API ENDPOINT (Visual & Interactive)

**Start the backend:**
```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader
./start-local.sh
```

**Option A: Interactive API Testing**
1. Open browser: http://localhost:8000/docs
2. Find "GET /api/market/indicators/rsi/{ticker}"
3. Click "Try it out"
4. Enter ticker (e.g., AAPL, VFV, ZQQ)
5. Click "Execute"
6. See JSON response with:
   - `current_value`: RSI value (0-100)
   - `signal`: BUY / SELL / HOLD
   - `confidence`: Confidence score
   - `recent_history`: Last 5 days

**Option B: Command Line**
```bash
# Basic test (AAPL with defaults: period=14, lookback=30)
curl "http://localhost:8000/api/market/indicators/rsi/AAPL"

# Custom period (20 instead of 14)
curl "http://localhost:8000/api/market/indicators/rsi/MSFT?period=20"

# Extended lookback (60 days instead of 30)
curl "http://localhost:8000/api/market/indicators/rsi/VFV?lookback=60"

# Pretty print JSON response
curl -s "http://localhost:8000/api/market/indicators/rsi/ZQQ" | python -m json.tool

# Test multiple tickers
for ticker in AAPL MSFT GOOGL VFV ZQQ; do
  echo "Testing $ticker:"
  curl -s "http://localhost:8000/api/market/indicators/rsi/$ticker" | grep '"signal"'
done
```

---

### 3️⃣ INTERACTIVE PYTHON TEST (For Learning)

**Start Python:**
```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader
source venv/bin/activate
cd backend
python
```

**In Python shell:**
```python
# Import RSI
from signals.indicators import RSI
import pandas as pd

# Create RSI calculator (14-period)
rsi = RSI(period=14)

# Create test data
prices = pd.Series([100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                    111, 110, 112, 114, 113, 115, 117, 116, 118, 120,
                    119, 121, 123, 122, 124, 126, 125, 127, 129, 128])

# Calculate RSI values
rsi_values = rsi.calculate(prices)

# Get current RSI
current_rsi = rsi_values.iloc[-1]
print(f"Current RSI: {current_rsi:.2f}")

# Get signal
signal = rsi.get_signal(current_rsi)
print(f"Signal: {signal}")

# Get confidence
confidence = rsi.get_confidence(current_rsi)
print(f"Confidence: {confidence:.1f}%")

# Test with your own data
my_prices = pd.Series([...your prices...])
my_rsi = rsi.calculate(my_prices)
```

**Exit Python:**
```python
exit()
```

---

### 4️⃣ TEST WITH REAL MARKET DATA (If network available)

```python
# In Python shell
import yfinance as yf
from signals.indicators import RSI

# Download AAPL data
data = yf.download('AAPL', period='3mo', progress=False)

# Calculate RSI
rsi = RSI(period=14)
rsi_values = rsi.calculate(data['Close'])

# Show last 5 RSI values
for i in range(-5, 0):
    date = data.index[i]
    price = data['Close'].iloc[i]
    rsi_val = rsi_values.iloc[i]
    signal = rsi.get_signal(rsi_val)
    print(f"{date.date()} | Price: ${price:.2f} | RSI: {rsi_val:.2f} | Signal: {signal}")
```

---

## Test Cases Included

### Test 1: Basic Calculation ✅
- Calculates RSI correctly with standard 14-period
- Verifies signal generation
- Checks confidence scoring

### Test 2: Real Market Data ✅
- Fetches actual stock data
- Calculates daily RSI values
- Shows trading interpretation

### Test 3: Signal Generation ✅
- BUY at RSI 25 (72.5% confidence)
- SELL at RSI 75 (72.5% confidence)
- HOLD in neutral zone (30-70)

### Test 4: Error Handling ✅
- Returns NaN with insufficient data
- Doesn't crash on edge cases
- Handles division by zero

---

## Expected Results

### Normal Output
```
Price: $128.00
RSI: 78.12
Signal: SELL
Confidence: 74.1%
Interpretation: OVERBOUGHT - Consider selling!
```

### All Tests Pass
```
✅ TEST 1 PASSED - Basic RSI
✅ TEST 2 PASSED - Real Data (if network available)
✅ TEST 3 PASSED - Signal Generation
✅ TEST 4 PASSED - Error Handling
✅ ALL TESTS COMPLETED SUCCESSFULLY
```

---

## Quick Test Commands

```bash
# Run all tests
python backend/signals/test_rsi.py

# Test RSI for 5 tickers via API
curl -s "http://localhost:8000/api/market/indicators/rsi/AAPL" | grep signal
curl -s "http://localhost:8000/api/market/indicators/rsi/MSFT" | grep signal
curl -s "http://localhost:8000/api/market/indicators/rsi/VFV" | grep signal
curl -s "http://localhost:8000/api/market/indicators/rsi/ZQQ" | grep signal

# Interactive browser testing
# Open: http://localhost:8000/docs
# Then click "GET /api/market/indicators/rsi/{ticker}"
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'signals'"
- Make sure you're in `backend/` directory before running Python
- Activate venv first: `source venv/bin/activate`

### "Address already in use" on port 8000
- Kill existing process: `pkill -f "uvicorn main:app"`
- Or use different port: `python -m uvicorn main:app --port 8001`

### "No data fetched from yfinance"
- Network connection issue
- Tests still pass for basic RSI calculation
- API endpoint will work if yfinance works later

### RSI values all NaN
- Need at least 15 data points (14 for calculation + 1)
- Provide more historical data

---

## Next Steps

Once RSI is working well:
1. Move to MACD indicator (Step 2)
2. Add MACD API endpoint
3. Create combined signal generator
4. Build risk engine

Ready to test? Run:
```bash
python backend/signals/test_rsi.py
```
