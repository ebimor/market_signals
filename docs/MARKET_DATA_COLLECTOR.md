# Market Data Collector Documentation

## Overview

The market data collector is a free, lightweight module that fetches real-time and historical market data for:
- **US Stocks**: Popular stocks tradable in Canada
- **Canadian ETFs**: From BMO, RBC, iShares, and Vanguard

It uses **Yahoo Finance** via the `yfinance` library, which is completely free and requires no API keys.

## Features

### 1. Real-Time Price Data
```python
from market_data.data_fetcher import get_fetcher

fetcher = get_fetcher()
price = fetcher.get_current_price("AAPL")
print(f"AAPL: ${price}")
```

### 2. Historical Data (Multiple Timeframes)
```python
# Daily data for the last year
data = fetcher.get_historical_data("AAPL", period="1y", interval="1d")

# Weekly data for the last 5 years
data = fetcher.get_historical_data("AAPL", period="5y", interval="1wk")

# Monthly data all-time
data = fetcher.get_historical_data("AAPL", period="max", interval="1mo")
```

### 3. Intraday Data
```python
# 5-minute candles for the last 5 days
data = fetcher.get_intraday_data("AAPL", interval="5m", days=5)

# 1-minute candles for today
data = fetcher.get_intraday_data("AAPL", interval="1m", days=1)
```

**Supported intervals:** `1m`, `5m`, `15m`, `30m`, `60m`, `1d`, `1wk`, `1mo`

### 4. Ticker Information
```python
info = fetcher.get_ticker_info("AAPL")
# Returns: name, sector, industry, market_cap, pe_ratio, dividend_yield, etc.
```

### 5. Batch Processing
```python
tickers = ["AAPL", "VFV", "XUS"]
data = fetcher.get_multiple_tickers(tickers, period="1mo")
# Returns dict: {"AAPL": DataFrame, "VFV": DataFrame, ...}
```

### 6. Built-in Caching
- Cache TTL: 5 minutes (configurable)
- Automatic cache validation
- Cache statistics

```python
stats = fetcher.get_cache_stats()
# Returns: {"total_cached": 5, "valid_cached": 4, "expired_cached": 1}
```

## Supported Tickers

### US Stocks (Partial List)
**Tech:** AAPL, MSFT, GOOGL, NVDA, TSLA, META, AMZN
**Finance:** JPM, BAC, WFC, GS
**Healthcare:** UNH, JNJ, PFE, ABBV, LLY
**Energy:** XOM, CVX, COP
**Broad Market ETFs:** SPY, QQQ, IWM, DIA

**Full list in:** [ticker_lists.py](ticker_lists.py)

### Canadian ETFs

**BMO ETFs:**
- ZSP - BMO S&P 500 Index ETF
- ZUE - BMO US Equity Index ETF
- ZCS - BMO Canadian Equity ETF
- ZNQ - BMO NASDAQ 100 Index ETF

**iShares ETFs:**
- XUS - iShares Core U.S. Index ETF
- XUU - iShares U.S. Index ETF
- XUL - iShares U.S. Dividend Aristocrats ETF
- XCB - iShares Canadian Corporate Bond Index ETF

**Vanguard ETFs:**
- VFV - Vanguard US Index ETF
- VSP - Vanguard US Total Market Index ETF
- VUN - Vanguard U.S. Total Market Diversified Index ETF
- VRE - Vanguard Real Estate Index ETF

**RBC ETFs:**
- RFV - RBC U.S. Index ETF
- RSP - RBC U.S. Index ETF (Unhedged)
- RBC - RBC Canadian Equity ETF

## API Endpoints

### Market Data Routes
Base URL: `/api/market`

#### Get Current Price
```
GET /api/market/price/{ticker}
```
Response:
```json
{
  "symbol": "AAPL",
  "current_price": 189.50,
  "timestamp": "2026-05-13T14:30:00"
}
```

#### Fetch & Store Candles
```
POST /api/market/candles/fetch
```
Request:
```json
{
  "ticker": "AAPL",
  "period": "1mo",
  "interval": "1d"
}
```

#### Get Stored Candles
```
GET /api/market/candles/{ticker}?interval=1d&limit=100
```

#### Get Market Health
```
GET /api/market/market-health
```
Response:
```json
{
  "timestamp": "2026-05-13T14:30:00",
  "is_market_healthy": true,
  "risk_level": "LOW",
  "vix": 15.2,
  "spy": 5234.5,
  "prices": {
    "^GSPC": 5234.5,
    "^VIX": 15.2,
    "^DJI": 42000.0
  }
}
```

### Stock Management

#### Get Stock
```
GET /api/market/stocks/{ticker}
```

#### List Stocks
```
GET /api/market/stocks?skip=0&limit=50&etf_type=BMO_ETF
```

#### Seed Default Stocks
```
POST /api/market/stocks/seed-default
```

### Watchlist Management

#### Create Watchlist
```
POST /api/market/watchlists
```
Request:
```json
{
  "name": "My Favorites",
  "description": "Stocks I'm watching",
  "is_default": false
}
```

#### List Watchlists
```
GET /api/market/watchlists
```

#### Get Watchlist with Items
```
GET /api/market/watchlists/{watchlist_id}
```

#### Add to Watchlist
```
POST /api/market/watchlists/{watchlist_id}/items/{stock_id}
```

#### Remove from Watchlist
```
DELETE /api/market/watchlists/{watchlist_id}/items/{stock_id}
```

#### Initialize Default Watchlist
```
POST /api/market/watchlists/init-default
```

### Signals

#### List Signals
```
GET /api/market/signals?is_active=true&signal_type=BUY&limit=50
```

#### Market Statistics
```
GET /api/market/stats
```
Response:
```json
{
  "stocks_in_db": 150,
  "candles_in_db": 45000,
  "watchlists": 5,
  "active_signals": 12,
  "cache": {
    "total_cached": 8,
    "valid_cached": 6,
    "expired_cached": 2
  }
}
```

## Data Model

### Stock
```python
class Stock:
    id: int
    symbol: str           # "AAPL", "VFV", etc.
    name: str            # Company/ETF name
    etf_type: str        # "US_STOCK", "BMO_ETF", etc.
    sector: str
    industry: str
    market_cap: float
    last_updated: datetime
```

### Candle
```python
class Candle:
    id: int
    stock_id: int
    timestamp: datetime
    interval: str        # "1d", "5m", etc.
    open: float
    high: float
    low: float
    close: float
    volume: int
    created_at: datetime
```

### Watchlist
```python
class Watchlist:
    id: int
    name: str
    description: str
    is_default: bool
    created_at: datetime
    items: List[WatchlistItem]  # Relationship
```

## Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Backend
```bash
python main.py
```
API will be available at `http://localhost:8000`

### 3. Test Market Data
```bash
python test_market_data.py
```

### 4. Access API Documentation
Open browser: `http://localhost:8000/docs`

## Testing

Run the test suite:
```bash
python test_market_data.py
```

Tests include:
- ✅ Single ticker price fetching
- ✅ Canadian ETF data
- ✅ Default watchlist
- ✅ Market health indicators
- ✅ Caching functionality

## Performance Considerations

### Caching Strategy
- Cache TTL: 5 minutes
- Per-ticker caching
- Automatic cache validation
- Reduces API calls to Yahoo Finance

### Data Storage
- Candles stored in SQLite/PostgreSQL
- Index on (stock_id, timestamp) for fast queries
- Efficient batch inserts

### Rate Limiting
- Yahoo Finance: No official rate limit, but practical limit ~2000 requests/hour
- yfinance handles throttling automatically
- Caching reduces actual requests

## Limitations

1. **Yahoo Finance Limitations**
   - No real-time bid/ask spreads
   - Delayed options data
   - No level 2 market data

2. **Data Freshness**
   - Daily data: Updated after market close
   - Intraday data: Updated during market hours
   - Caching: 5-minute TTL

## Advanced Usage

### Custom Fetch Interval
```python
# Fetch every 5 minutes
fetcher = MarketDataFetcher(cache_ttl_minutes=5)
```

### Batch Operations
```python
# Fetch for multiple tickers at once
tickers = ["AAPL", "VFV", "XUS"]
data = fetcher.get_multiple_tickers(tickers, period="1y")

for ticker, df in data.items():
    if df is not None:
        print(f"{ticker}: {len(df)} candles")
```

### Market Health Checks
```python
# Get market health and adjust trading based on conditions
health = fetcher.get_market_health_tickers()
vix = fetcher.get_current_price("^VIX")

if vix > 30:
    print("Market volatility too high - disable new trades")
else:
    print("Market looks good - proceed with trading")
```

## Integration with Signal Engine

The market data collector integrates seamlessly with the signal engine:

```python
# Get data
data = fetcher.get_historical_data("AAPL", period="1mo")

# Calculate indicators
rsi = calculate_rsi(data['close'])
macd = calculate_macd(data['close'])

# Generate signals based on indicators
if rsi < 30 and macd_bullish:
    signal = "BUY"
```

## Support & Troubleshooting

### Issue: "No data returned for ticker"
- Check ticker symbol (e.g., AAPL not apple)
- Verify ticker is tradable in Canada
- Try again after market hours

### Issue: "API rate limit exceeded"
- Wait a few minutes
- Caching should minimize this
- Use batch operations when possible

### Issue: "Connection timeout"
- Check internet connection
- Yahoo Finance may be temporarily unavailable
- Try again in a few moments

## Future Enhancements

- [ ] Support for multiple data providers (Polygon, Finnhub)
- [ ] Options data
- [ ] Level 2 market data
- [ ] Real-time WebSocket updates
- [ ] Fundamental data (earnings, dividends)
- [ ] Corporate actions handling
