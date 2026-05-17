# Market Data Collector - Getting Started Guide

## 🎯 What You Just Built

A **free, production-ready market data collector** that:
- Fetches real-time and historical data for US stocks and Canadian ETFs
- Stores data in SQLite or PostgreSQL
- Provides REST API endpoints for easy access
- Includes intelligent caching to reduce API calls
- Supports multiple timeframes (1m, 5m, 1d, 1w, 1mo, etc.)

## 📊 Supported Securities

### US Stocks (60+ tickers)
All major stocks tradable in Canada: AAPL, MSFT, GOOGL, NVDA, TSLA, AMZN, JPM, UNH, XOM, WMT, KO, and more

### Canadian ETFs (25+ tickers)

| Provider | Tickers | Focus |
|----------|---------|-------|
| **BMO** | ZSP, ZUE, ZCS, ZNQ | Index, Equity, NASDAQ |
| **iShares** | XUS, XUU, XUL, XCB | US Equity, Corporate Bonds |
| **Vanguard** | VFV, VSP, VUN, VAB | US Index, Bond Index |
| **RBC** | RFV, RSP, RBC | US Equity |

### Market Indices
S&P 500, NASDAQ, Dow Jones, VIX, TSX

## 🚀 Quick Start (5 minutes)

### Step 1: Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

Or use the quick start script:
```bash
bash quickstart.sh
```

### Step 2: Start the Backend
```bash
python main.py
```

You'll see:
```
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 3: Test It Out
Visit: **http://localhost:8000/docs**

You'll see interactive API documentation with all endpoints!

## 💻 Usage Examples

### Example 1: Get Current Stock Price
```bash
curl http://localhost:8000/api/market/price/AAPL
```

Response:
```json
{
  "symbol": "AAPL",
  "current_price": 189.50,
  "timestamp": "2026-05-13T14:30:00"
}
```

### Example 2: Fetch 1 Month of Daily Candles
```bash
curl -X POST http://localhost:8000/api/market/candles/fetch \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "VFV",
    "period": "1mo",
    "interval": "1d"
  }'
```

### Example 3: Get Market Health (Risk Assessment)
```bash
curl http://localhost:8000/api/market/market-health
```

Response:
```json
{
  "timestamp": "2026-05-13T14:30:00",
  "is_market_healthy": true,
  "risk_level": "LOW",
  "vix": 15.2,
  "spy": 5234.50,
  "prices": {
    "^GSPC": 5234.50,
    "^VIX": 15.2,
    "^DJI": 42000.0
  }
}
```

### Example 4: Create a Watchlist
```bash
# First, seed default stocks
curl -X POST http://localhost:8000/api/market/stocks/seed-default

# Then initialize default watchlist
curl -X POST http://localhost:8000/api/market/watchlists/init-default

# Get the watchlist
curl http://localhost:8000/api/market/watchlists
```

### Example 5: Python Usage (Programmatic)
```python
from market_data.data_fetcher import get_fetcher

fetcher = get_fetcher()

# Get Canadian ETF price
price = fetcher.get_current_price("VFV")
print(f"VFV: ${price}")

# Get 1-year daily data
data = fetcher.get_historical_data("XUS", period="1y", interval="1d")
print(f"Got {len(data)} candles")
print(data.tail())

# Get intraday 5-minute data
intraday = fetcher.get_intraday_data("AAPL", interval="5m", days=5)
print(f"Got {len(intraday)} 5-minute candles")

# Check market health
vix = fetcher.get_current_price("^VIX")
print(f"VIX: {vix}")
if vix > 30:
    print("HIGH VOLATILITY - SKIP NEW TRADES")
```

## 📁 Project Structure

```
backend/
├── main.py                    # FastAPI app
├── config.py                 # Configuration
├── requirements.txt          # Dependencies
├── test_market_data.py       # Test script
│
├── market_data/
│   ├── data_fetcher.py      # Yahoo Finance integration
│   └── ticker_lists.py      # US stocks & Canadian ETFs
│
├── database/
│   ├── models.py            # SQLAlchemy models
│   └── db.py                # Database setup
│
└── api/
    ├── schemas.py           # Pydantic models
    └── routes.py            # REST endpoints
```

## 🔌 REST API Reference

### Market Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/market/price/{ticker}` | Current price |
| POST | `/api/market/candles/fetch` | Fetch & store candles |
| GET | `/api/market/candles/{ticker}` | Get stored candles |
| GET | `/api/market/market-health` | Market health & risk |
| GET | `/api/market/stocks/{ticker}` | Stock info |
| GET | `/api/market/stocks` | List stocks |
| POST | `/api/market/stocks/seed-default` | Seed default stocks |

### Watchlists

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/market/watchlists` | List watchlists |
| POST | `/api/market/watchlists` | Create watchlist |
| GET | `/api/market/watchlists/{id}` | Get watchlist |
| POST | `/api/market/watchlists/{id}/items/{stock_id}` | Add stock |
| DELETE | `/api/market/watchlists/{id}/items/{stock_id}` | Remove stock |
| POST | `/api/market/watchlists/init-default` | Initialize default |

### Signals & Stats

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/market/signals` | List signals |
| GET | `/api/market/stats` | Database statistics |

## 🎓 Understanding the Data Model

### Stock
Master data for each ticker:
- Symbol (e.g., "AAPL", "VFV")
- Name, sector, industry
- Market cap

### Candle (OHLCV)
Price bars at different intervals:
- Open, High, Low, Close, Volume
- Timestamp and interval (1m, 5m, 1d, etc.)
- Indexed for fast queries

### Watchlist
User-created collections of stocks:
- Name and description
- Default watchlist available
- Can have multiple items

### Signal
Trading signals generated by the system:
- Type: BUY, SELL, HOLD
- Confidence/strength (0-100)
- Suggested entry, stop loss, take profit

## ⚙️ Configuration

Edit `backend/.env` to customize:

```env
# API Settings
API_PORT=8000
DEBUG=True

# Database (default is SQLite)
DATABASE_URL=sqlite:///./safeswing.db
# For PostgreSQL: postgresql://user:password@localhost/safeswing

# Market Data Refresh (seconds)
MARKET_DATA_REFRESH_INTERVAL=60

# Risk Management
DEFAULT_ACCOUNT_RISK_PERCENT=0.01  # 1% per trade
DEFAULT_STOP_LOSS_ATR_MULTIPLIER=1.5
DEFAULT_TAKE_PROFIT_RATIO=2.0      # 2:1 reward/risk

# Signal Engine
VIX_THRESHOLD=30.0  # Disable trades above this VIX level
```

## 🧪 Running Tests

```bash
cd backend
python test_market_data.py
```

Tests include:
- Single ticker fetching
- Canadian ETF data
- Default watchlist
- Market health indicators
- Caching validation

## 📊 Data Timeframes Supported

| Interval | Description | Typical Use |
|----------|-------------|------------|
| 1m | 1-minute bars | Intraday scalping |
| 5m | 5-minute bars | Intraday trading |
| 15m | 15-minute bars | Intraday analysis |
| 30m | 30-minute bars | Intraday swings |
| 60m | 1-hour bars | Swing trading |
| 1d | Daily bars | Swing trading |
| 1wk | Weekly bars | Long-term trends |
| 1mo | Monthly bars | Long-term analysis |

## 🔄 Data Flow

```
┌─────────────────┐
│  Frontend App   │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│   FastAPI App   │
└────────┬────────┘
         │
         ├─────────────────────┐
         │                     │
         ▼                     ▼
   ┌──────────────┐     ┌──────────────┐
   │  API Routes  │     │   DB Models  │
   └──────┬───────┘     └──────┬───────┘
          │                    │
          ▼                    ▼
   ┌──────────────┐     ┌──────────────┐
   │  Data Fetcher│     │  SQLite/PG   │
   └──────┬───────┘     └──────────────┘
          │
          ▼
   ┌──────────────┐
   │ Yahoo Finance│ (FREE!)
   └──────────────┘
```

## 💡 Key Features

✅ **Free** - No API keys or subscriptions needed  
✅ **Real-time** - Live market data during trading hours  
✅ **Historical** - Years of historical data  
✅ **Multiple timeframes** - 1m to monthly candles  
✅ **Caching** - Intelligent 5-minute cache to reduce API calls  
✅ **Database** - SQLite default, PostgreSQL ready  
✅ **REST API** - Interactive Swagger documentation  
✅ **Canada-focused** - US stocks + Canadian ETFs  
✅ **Error handling** - Graceful API failures  
✅ **Logging** - Detailed operation logs  

## 🚨 Error Handling

The system gracefully handles:
- Invalid ticker symbols
- Network timeouts
- Rate limiting
- Missing data
- Database errors

All errors are logged and returned with helpful messages.

## 📈 Next Steps

1. **Signal Engine** - Generate buy/sell signals based on technical indicators
2. **Risk Engine** - Position sizing and portfolio protection
3. **Backtesting** - Test strategies on historical data
4. **Frontend** - Build React dashboard
5. **Broker Integration** - Connect to Alpaca for paper/live trading

## 🆘 Troubleshooting

### "Connection Error"
- Check internet connection
- Yahoo Finance may be temporarily unavailable
- Try again in a few moments

### "No data returned"
- Verify ticker symbol (e.g., "AAPL" not "Apple")
- Market may be closed
- Try a different time period

### "Database locked"
- SQLite can have concurrency issues
- Switch to PostgreSQL for production
- Or ensure only one process accesses the DB

## 📚 Documentation

- **[Market Data Collector Guide](./docs/MARKET_DATA_COLLECTOR.md)** - Detailed documentation
- **[Implementation Summary](./docs/IMPLEMENTATION_SUMMARY.md)** - What was built
- **[API Docs](http://localhost:8000/docs)** - Interactive documentation (when running)

## 🎯 What Makes This Special

1. **100% Free** - No paid APIs or subscriptions
2. **Canada-Ready** - US stocks + Canadian ETFs from all major providers
3. **Production-Ready** - Error handling, logging, caching
4. **Type-Safe** - Python type hints + Pydantic validation
5. **REST API** - Easy to integrate with frontend
6. **Extensible** - Easy to add new data sources or indicators

## 📞 Support

For issues or questions:
1. Check the documentation files
2. Review the test script: `python test_market_data.py`
3. Check logs in the running terminal
4. Verify `.env` configuration

---

**Ready to build the signal engine next?** 🚀

The foundation is solid. Next, we'll add:
- Technical indicator calculations (RSI, MACD, EMA, ATR)
- Conservative signal generation logic
- Market health assessment
- Risk management calculations
