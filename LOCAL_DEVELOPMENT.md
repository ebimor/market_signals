# SafeSwing Trader - Local Development Setup

## Current Status

✅ **Backend**: Running on http://localhost:8000
📦 **Dependencies**: Installed via virtual environment
🐳 **Docker**: Network issues in container environment

## Quick Start (Local)

### 1. Activate Virtual Environment
```bash
cd /home/eshahrivar/test_hedge_ai/safeswing_trader
source venv/bin/activate
```

### 2. Start Backend Server
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Server will be available at:**
- API Docs: http://localhost:8000/docs
- API: http://localhost:8000/api/

### 3. Test the API
```bash
# Get current price
curl http://localhost:8000/api/market/price/AAPL

# Get historical data
curl http://localhost:8000/api/market/candles/AAPL

# List all watchlists
curl http://localhost:8000/api/market/watchlists
```

## Project Structure

```
safeswing_trader/
├── backend/                  # FastAPI backend
│   ├── main.py             # FastAPI app entry
│   ├── config.py           # Configuration
│   ├── requirements.txt     # Backend dependencies
│   ├── database/           # SQLAlchemy models & DB setup
│   ├── market_data/        # Data fetching (yfinance)
│   └── api/                # REST API routes & schemas
├── frontend/               # React frontend
│   ├── src/               # React components & pages
│   └── package.json       # Frontend dependencies
├── venv/                   # Python virtual environment
├── docker-compose.yml      # Docker orchestration (optional)
├── requirements-local.txt  # Simplified dependencies (no ta-lib)
└── README.md              # Project documentation
```

## Included Tickers

### US Stocks (60+)
AAPL, MSFT, GOOGL, NVDA, TSLA, JPM, BAC, etc.

### Canadian ETFs (25+)
- **BMO**: ZSP, ZUE, ZCS
- **iShares**: XUS, XUU, XCB
- **Vanguard**: VFV, VSP, VAB
- **RBC**: RFV, RSP
- **Leveraged**: **ZQQ** (3x NASDAQ), HQQ (2x inverse NASDAQ)

### Market Indices
^GSPC, ^VIX, ^DJI, ^IXIC, ^GSPTSE

## API Endpoints (20+)

**Market Data:**
- `GET /api/market/price/{ticker}` - Current price
- `GET /api/market/candles/{ticker}` - Historical OHLCV data
- `GET /api/market/market-health` - Market overview

**Watchlists:**
- `GET /api/market/watchlists` - List all watchlists
- `POST /api/market/watchlists` - Create watchlist
- `POST /api/market/watchlist/{id}/items` - Add ticker
- `DELETE /api/market/watchlist/{id}/items/{ticker}` - Remove ticker

**Signals:**
- `GET /api/market/signals` - Trading signals
- `GET /api/market/stats` - Statistics

See `/docs` for interactive API documentation.

## Development Notes

### Backend Development
1. Edit files in `backend/`
2. Server auto-reloads with `--reload` flag
3. Refresh browser to see changes
4. Check `/tmp/backend.log` for errors

### Database
- Uses SQLite by default (`safeswing.db`)
- Models defined in `backend/database/models.py`
- 8 tables: Stock, Candle, Indicator, Watchlist, WatchlistItem, Trade, Signal, MarketHealth

### Data Fetching
- Uses **yfinance** (100% free, no API keys)
- 5-minute intelligent caching
- Supports 1m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo intervals

## Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
lsof -i :8000
# Kill the process
kill -9 <PID>
```

### Package import errors
```bash
# Reinstall dependencies
pip install -r requirements-local.txt
```

### yfinance not fetching data
- Check network connectivity
- Verify ticker symbols are correct
- yfinance requires internet access

## Docker (Optional)

If Docker network access is restored:
```bash
# Build backend image
docker-compose build --no-cache backend

# Start all services
docker-compose up
```

## Next Steps

1. ✅ Market data collector (complete)
2. 📋 Signal engine (Phase 2) - Technical indicators & trading signals
3. 📊 Risk engine (Phase 3) - Position sizing & stop-losses
4. 🧪 Backtesting engine (Phase 4) - Historical strategy testing
5. 🎨 Frontend dashboard (Phase 5) - React UI with charts
6. 💹 Broker integration (Phase 6) - Alpaca API for live trading

## Project Stats

- **Files Created**: 30+
- **API Endpoints**: 20+
- **Database Models**: 8
- **Supported Tickers**: 85+
- **Data Source**: Yahoo Finance (free)
- **Free**: Yes! No API keys required
