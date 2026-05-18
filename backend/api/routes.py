"""
Market data API routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import logging
import pandas as pd

from backend.database.db import get_db
from backend.database.models import Stock, Candle, Watchlist, WatchlistItem, Signal
from backend.market_data.data_fetcher import get_fetcher
from backend.signals.indicators import RSI, calculate_rsi
from backend.risk.risk_engine import RiskEngine
from backend.market_data.ticker_lists import (
    ALL_TICKERS,
    CANADIAN_ETFS,
    get_default_watchlist,
    get_market_health_tickers,
)
from backend.api.schemas import (
    StockResponse,
    StockCreate,
    CandleResponse,
    PriceDataResponse,
    HistoricalDataRequest,
    WatchlistResponse,
    WatchlistCreate,
    WatchlistWithItems,
    SignalResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/market", tags=["market"])


# ============================================================================
# Stock Endpoints
# ============================================================================

@router.get("/stocks/{ticker}", response_model=StockResponse)
async def get_stock(ticker: str, db: Session = Depends(get_db)):
    """Get stock information"""
    stock = db.query(Stock).filter(Stock.symbol == ticker.upper()).first()
    
    if not stock:
        # Try to fetch from Yahoo Finance and create
        fetcher = get_fetcher()
        info = fetcher.get_ticker_info(ticker)
        
        if not info:
            raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
        
        stock = Stock(
            symbol=ticker.upper(),
            name=info.get("name"),
            market_cap=info.get("market_cap"),
        )
        db.add(stock)
        db.commit()
        db.refresh(stock)
    
    return stock


@router.get("/stocks", response_model=List[StockResponse])
async def list_stocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    etf_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List stocks in database"""
    query = db.query(Stock)
    
    if etf_type:
        query = query.filter(Stock.etf_type == etf_type)
    
    stocks = query.offset(skip).limit(limit).all()
    return stocks


@router.post("/stocks/seed-default", response_model=dict)
async def seed_default_stocks(db: Session = Depends(get_db)):
    """Seed default stocks and ETFs to database"""
    created_count = 0
    
    for ticker in ALL_TICKERS:
        existing = db.query(Stock).filter(Stock.symbol == ticker).first()
        if existing:
            continue
        
        # Determine ETF type
        etf_type = None
        if ticker in CANADIAN_ETFS:
            if ticker[:3] == "ZSP" or ticker[:1] == "Z":
                etf_type = "BMO_ETF"
            elif ticker[:1] == "X":
                etf_type = "ISHARES_ETF"
            elif ticker[:1] == "V":
                etf_type = "VANGUARD_ETF"
            elif ticker[:3] == "RBC" or ticker[:1] == "R":
                etf_type = "RBC_ETF"
            else:
                etf_type = "CANADIAN_ETF"
        else:
            etf_type = "US_STOCK"
        
        stock = Stock(symbol=ticker, etf_type=etf_type)
        db.add(stock)
        created_count += 1
    
    db.commit()
    logger.info(f"Seeded {created_count} stocks/ETFs")
    return {"created": created_count, "message": f"Seeded {created_count} stocks/ETFs"}


# ============================================================================
# Price and Candle Endpoints
# ============================================================================

@router.get("/price/{ticker}", response_model=PriceDataResponse)
async def get_current_price(ticker: str):
    """Get current price for a ticker"""
    fetcher = get_fetcher()
    price = fetcher.get_current_price(ticker)
    
    if price is None:
        raise HTTPException(status_code=404, detail=f"Could not fetch price for {ticker}")
    
    return PriceDataResponse(
        symbol=ticker.upper(),
        current_price=price,
        timestamp=datetime.utcnow()
    )


@router.post("/candles/fetch")
async def fetch_and_store_candles(
    request: HistoricalDataRequest,
    db: Session = Depends(get_db)
):
    """Fetch historical candles and store in database"""
    fetcher = get_fetcher()
    ticker = request.ticker.upper()
    
    # Fetch data from Yahoo Finance
    data = fetcher.get_historical_data(ticker, period=request.period, interval=request.interval)
    if data is None or data.empty:
        raise HTTPException(status_code=404, detail=f"No data found for {ticker}")
    
    # Get or create stock
    stock = db.query(Stock).filter(Stock.symbol == ticker).first()
    if not stock:
        stock = Stock(symbol=ticker)
        db.add(stock)
        db.flush()
    
    # Store candles
    stored_count = 0
    for timestamp, row in data.iterrows():
        # Check if candle already exists
        existing = db.query(Candle).filter(
            Candle.stock_id == stock.id,
            Candle.timestamp == timestamp,
            Candle.interval == request.interval
        ).first()
        
        if existing:
            continue
        
        candle = Candle(
            stock_id=stock.id,
            timestamp=timestamp,
            interval=request.interval,
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
            volume=int(row['volume']) if 'volume' in row else None,
        )
        db.add(candle)
        stored_count += 1
    
    db.commit()
    logger.info(f"Stored {stored_count} candles for {ticker}")
    
    return {
        "symbol": ticker,
        "interval": request.interval,
        "stored": stored_count,
        "period": request.period
    }


@router.get("/candles/{ticker}", response_model=List[CandleResponse])
async def get_candles(
    ticker: str,
    interval: str = Query("1d"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get historical candles for a ticker"""
    stock = db.query(Stock).filter(Stock.symbol == ticker.upper()).first()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    
    candles = db.query(Candle).filter(
        Candle.stock_id == stock.id,
        Candle.interval == interval
    ).order_by(Candle.timestamp.desc()).limit(limit).all()
    
    return list(reversed(candles))


@router.get("/market-health")
async def get_market_health():
    """Get market health indicators (SPY, VIX, etc.)"""
    fetcher = get_fetcher()
    health_tickers = get_market_health_tickers()
    
    prices = {}
    for ticker in health_tickers:
        price = fetcher.get_current_price(ticker)
        if price:
            prices[ticker] = price
    
    # Assess market health
    spy_price = prices.get("^GSPC")
    vix_price = prices.get("^VIX")
    
    is_healthy = True
    risk_level = "LOW"
    
    if vix_price and vix_price > 30:
        is_healthy = False
        risk_level = "HIGH"
    elif vix_price and vix_price > 20:
        risk_level = "MEDIUM"
    
    return {
        "timestamp": datetime.utcnow(),
        "prices": prices,
        "is_market_healthy": is_healthy,
        "risk_level": risk_level,
        "vix": vix_price,
        "spy": spy_price,
    }


# ============================================================================
# Watchlist Endpoints
# ============================================================================

@router.get("/watchlists", response_model=List[WatchlistResponse])
async def list_watchlists(db: Session = Depends(get_db)):
    """List all watchlists"""
    watchlists = db.query(Watchlist).all()
    return watchlists


@router.post("/watchlists", response_model=WatchlistResponse)
async def create_watchlist(
    watchlist: WatchlistCreate,
    db: Session = Depends(get_db)
):
    """Create a new watchlist"""
    db_watchlist = Watchlist(**watchlist.model_dump())
    db.add(db_watchlist)
    db.commit()
    db.refresh(db_watchlist)
    return db_watchlist


@router.get("/watchlists/{watchlist_id}", response_model=WatchlistWithItems)
async def get_watchlist(watchlist_id: int, db: Session = Depends(get_db)):
    """Get watchlist with items"""
    watchlist = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return watchlist


@router.post("/watchlists/{watchlist_id}/items/{stock_id}")
async def add_to_watchlist(watchlist_id: int, stock_id: int, db: Session = Depends(get_db)):
    """Add stock to watchlist"""
    watchlist = db.query(Watchlist).filter(Watchlist.id == watchlist_id).first()
    if not watchlist:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    
    stock = db.query(Stock).filter(Stock.id == stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    # Check if already in watchlist
    existing = db.query(WatchlistItem).filter(
        WatchlistItem.watchlist_id == watchlist_id,
        WatchlistItem.stock_id == stock_id
    ).first()
    
    if existing:
        return {"message": "Stock already in watchlist"}
    
    item = WatchlistItem(watchlist_id=watchlist_id, stock_id=stock_id)
    db.add(item)
    db.commit()
    return {"message": "Stock added to watchlist"}


@router.delete("/watchlists/{watchlist_id}/items/{stock_id}")
async def remove_from_watchlist(watchlist_id: int, stock_id: int, db: Session = Depends(get_db)):
    """Remove stock from watchlist"""
    item = db.query(WatchlistItem).filter(
        WatchlistItem.watchlist_id == watchlist_id,
        WatchlistItem.stock_id == stock_id
    ).first()
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not in watchlist")
    
    db.delete(item)
    db.commit()
    return {"message": "Stock removed from watchlist"}


@router.post("/watchlists/init-default")
async def init_default_watchlist(db: Session = Depends(get_db)):
    """Initialize default watchlist"""
    # Check if default exists
    default = db.query(Watchlist).filter(Watchlist.is_default == True).first()
    if default:
        return {"message": "Default watchlist already exists"}
    
    # Create default watchlist
    watchlist = Watchlist(
        name="Default",
        description="Default watchlist with popular US stocks and Canadian ETFs",
        is_default=True
    )
    db.add(watchlist)
    db.flush()
    
    # Add default stocks
    default_tickers = get_default_watchlist()
    for ticker in default_tickers:
        stock = db.query(Stock).filter(Stock.symbol == ticker).first()
        if not stock:
            stock = Stock(symbol=ticker)
            db.add(stock)
            db.flush()
        
        item = WatchlistItem(watchlist_id=watchlist.id, stock_id=stock.id)
        db.add(item)
    
    db.commit()
    return {
        "message": "Default watchlist initialized",
        "watchlist_id": watchlist.id,
        "stocks_added": len(default_tickers)
    }


# ============================================================================
# Technical Indicators Endpoints
# ============================================================================

def _generate_mock_price_data(ticker: str, lookback: int, interval: str = "1d") -> pd.DataFrame:
    """Generate mock price data when yfinance fails (for testing/sandbox)
    
    Args:
        ticker: Stock symbol
        lookback: Number of periods to generate
        interval: "1h" (hourly), "4h" (4-hour), "1d" (daily), "1wk" (weekly)
    """
    import numpy as np
    from datetime import datetime, timedelta
    
    # Different trends for different tickers for demo purposes
    base_prices = {
        'AAPL': 150,
        'TSLA': 250,
        'MSFT': 380,
        'GOOGL': 140,
        'AMZN': 170,
        'DEFAULT': 100
    }
    
    base = base_prices.get(ticker.upper(), base_prices['DEFAULT'])
    
    # Map interval to pandas frequency
    freq_map = {
        '1h': 'H',   # Hourly
        '4h': '4H',  # 4-hour
        '1d': 'D',   # Daily
        '1wk': 'W'   # Weekly
    }
    freq = freq_map.get(interval, 'D')
    
    # Generate trending data (slight uptrend with noise)
    dates = pd.date_range(end=datetime.now(), periods=lookback, freq=freq)
    trend = np.linspace(0, 20, lookback)  # Uptrend
    noise = np.random.normal(0, 2, lookback)
    prices = base + trend + noise
    
    df = pd.DataFrame({
        'Date': dates,
        'Close': prices,
        'Open': prices * 0.99,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Volume': np.random.randint(1000000, 100000000, lookback)
    })
    df.set_index('Date', inplace=True)
    return df


def _fetch_price_data(ticker: str, lookback: int, interval: str):
    """Fetch price data from yfinance; fall back to simulated data.

    Returns:
        (dataframe, is_simulated): is_simulated=True when yfinance was unavailable.
    """
    fetcher = get_fetcher()
    data = fetcher.get_historical_data(ticker, period=f"{lookback}d", interval=interval)
    if data is None or data.empty:
        logger.warning(f"yfinance unavailable for {ticker} — returning simulated data")
        return _generate_mock_price_data(ticker, min(lookback, 100), interval=interval), True
    return data, False


@router.get("/indicators/rsi/{ticker}")
async def get_rsi_indicator(
    ticker: str,
    period: int = Query(14, ge=2, le=50),
    lookback: int = Query(30, ge=1, le=365),
    interval: str = Query("1d", regex="^(1h|4h|1d|1wk)$"),
    db: Session = Depends(get_db)
):
    """
    Get RSI (Relative Strength Index) for a ticker across different timeframes.
    
    Args:
        ticker: Stock/ETF symbol
        period: RSI period (default: 14)
        lookback: Number of periods to fetch (default: 30)
        interval: Timeframe - "1h" (hourly), "4h" (4-hour), "1d" (daily), "1wk" (weekly)
    
    Returns:
        Current RSI value, signal, confidence, and recent history
    """
    try:
        ticker_upper = ticker.upper()

        data, is_simulated = _fetch_price_data(ticker_upper, lookback, interval)

        # Calculate RSI
        rsi_calc = RSI(period=period)
        rsi_values = rsi_calc.calculate(data['Close'])
        
        # Get current RSI (last value)
        current_rsi = float(rsi_values.iloc[-1]) if not pd.isna(rsi_values.iloc[-1]) else None
        
        if current_rsi is None:
            raise HTTPException(status_code=400, detail=f"Insufficient data for RSI calculation. Need at least {period + 1} data points.")
        
        # Get signal and confidence
        signal = rsi_calc.get_signal(current_rsi)
        confidence = rsi_calc.get_confidence(current_rsi)
        
        # Build response with recent history (last 5 days)
        recent_history = []
        for i in range(max(0, len(rsi_values)-5), len(rsi_values)):
            date = data.index[i]
            price = float(data['Close'].iloc[i])
            rsi_val = float(rsi_values.iloc[i]) if not pd.isna(rsi_values.iloc[i]) else None
            
            if rsi_val is not None:
                recent_history.append({
                    "date": date.isoformat(),
                    "price": price,
                    "rsi": round(rsi_val, 2),
                    "signal": rsi_calc.get_signal(rsi_val),
                })
        
        return {
            "ticker": ticker_upper,
            "indicator": "RSI",
            "period": period,
            "current_value": round(current_rsi, 2),
            "signal": signal,
            "confidence": round(confidence, 1),
            "interpretation": (
                "Oversold - Good buying opportunity" if current_rsi < 30 else
                "Overbought - Consider selling" if current_rsi > 70 else
                "Neutral - Wait for clear signal"
            ),
            "recent_history": recent_history,
            "data_source": "simulated" if is_simulated else "live",
            "last_updated": data.index[-1].isoformat() if not is_simulated else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating RSI for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating RSI: {str(e)}")


@router.get("/indicators/macd/{ticker}")
async def get_macd_indicator(
    ticker: str,
    fast: int = Query(12, ge=2, le=50),
    slow: int = Query(26, ge=2, le=100),
    signal: int = Query(9, ge=2, le=50),
    lookback: int = Query(30, ge=1, le=365),
    interval: str = Query("1d", regex="^(1h|4h|1d|1wk)$"),
    db: Session = Depends(get_db)
):
    """
    Get MACD (Moving Average Convergence Divergence) for a ticker across different timeframes.
    
    MACD consists of:
    - MACD Line: fast EMA - slow EMA
    - Signal Line: EMA of MACD Line
    - Histogram: MACD Line - Signal Line
    
    Args:
        ticker: Stock/ETF symbol
        fast: Fast EMA period (default: 12)
        slow: Slow EMA period (default: 26)
        signal: Signal line EMA period (default: 9)
        lookback: Number of periods to fetch (default: 30)
        interval: Timeframe - "1h" (hourly), "4h" (4-hour), "1d" (daily), "1wk" (weekly)
    
    Returns:
        Current MACD values, signal, histogram, and interpretation
    """
    try:
        from backend.signals.indicators import MACD

        ticker_upper = ticker.upper()

        data, is_simulated = _fetch_price_data(ticker_upper, lookback, interval)

        # Calculate MACD
        macd_calc = MACD(fast=fast, slow=slow, signal=signal)
        macd_line, signal_line, histogram = macd_calc.calculate(data['Close'])
        
        # Get current values (last value)
        current_macd = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
        current_signal = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None
        current_histogram = float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None
        
        if current_macd is None or current_signal is None:
            raise HTTPException(status_code=400, detail=f"Insufficient data for MACD calculation. Need at least {slow + 1} data points.")
        
        # Determine signal based on histogram and MACD/Signal relationship
        if current_histogram > 0 and macd_line.iloc[-2] < signal_line.iloc[-2]:
            # Bullish crossover (histogram positive and just crossed)
            macd_signal = "BUY"
            confidence = min(100, abs(current_histogram) * 100 + 30)
        elif current_histogram < 0 and macd_line.iloc[-2] > signal_line.iloc[-2]:
            # Bearish crossover (histogram negative and just crossed)
            macd_signal = "SELL"
            confidence = min(100, abs(current_histogram) * 100 + 30)
        elif current_histogram > 0 and current_macd > 0:
            # Bullish conditions
            macd_signal = "BUY"
            confidence = min(100, abs(current_histogram) * 100 + 20)
        elif current_histogram < 0 and current_macd < 0:
            # Bearish conditions
            macd_signal = "SELL"
            confidence = min(100, abs(current_histogram) * 100 + 20)
        else:
            # Neutral
            macd_signal = "HOLD"
            confidence = abs(current_histogram) * 50
        
        # Build response with recent history (last 5 periods)
        recent_history = []
        for i in range(max(0, len(data) - 5), len(data)):
            date = data.index[i]
            price = float(data['Close'].iloc[i])
            macd_val = float(macd_line.iloc[i]) if not pd.isna(macd_line.iloc[i]) else None
            signal_val = float(signal_line.iloc[i]) if not pd.isna(signal_line.iloc[i]) else None
            histogram_val = float(histogram.iloc[i]) if not pd.isna(histogram.iloc[i]) else None
            
            if macd_val is not None and signal_val is not None:
                recent_history.append({
                    "date": date.isoformat(),
                    "price": price,
                    "macd": round(macd_val, 4),
                    "signal": round(signal_val, 4),
                    "histogram": round(histogram_val, 4),
                })
        
        return {
            "ticker": ticker_upper,
            "indicator": "MACD",
            "parameters": {
                "fast": fast,
                "slow": slow,
                "signal": signal
            },
            "current": {
                "macd": round(current_macd, 4),
                "signal": round(current_signal, 4),
                "histogram": round(current_histogram, 4),
            },
            "signal": macd_signal,
            "confidence": round(confidence, 1),
            "interpretation": (
                "Bullish - Strong uptrend momentum" if macd_signal == "BUY" and current_histogram > 0 else
                "Bearish - Strong downtrend momentum" if macd_signal == "SELL" and current_histogram < 0 else
                "Neutral - Awaiting signal"
            ),
            "recent_history": recent_history,
            "data_source": "simulated" if is_simulated else "live",
            "last_updated": data.index[-1].isoformat() if not is_simulated else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating MACD for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating MACD: {str(e)}")


@router.get("/indicators/ema/{ticker}")
async def get_ema_indicator(
    ticker: str,
    period: int = Query(20, ge=2, le=200),
    lookback: int = Query(30, ge=1, le=365),
    interval: str = Query("1d", regex="^(1h|4h|1d|1wk)$"),
    db: Session = Depends(get_db)
):
    """
    Get EMA (Exponential Moving Average) for a ticker.
    
    EMA gives more weight to recent prices, reacting faster to price changes.
    Uses: Trend identification and confirmation
    
    Args:
        ticker: Stock/ETF symbol
        period: EMA period (default: 20)
        lookback: Number of periods to fetch (default: 30)
        interval: Timeframe - "1h", "4h", "1d" (default), "1wk"
    
    Returns:
        Current EMA value, price position relative to EMA, and recent history
    """
    try:
        from backend.signals.indicators import EMA

        ticker_upper = ticker.upper()

        data, is_simulated = _fetch_price_data(ticker_upper, lookback, interval)

        # Calculate EMA
        ema_calc = EMA(period=period)
        ema_values = ema_calc.calculate(data['Close'])
        
        # Get current values (last value)
        current_ema = float(ema_values.iloc[-1]) if not pd.isna(ema_values.iloc[-1]) else None
        current_price = float(data['Close'].iloc[-1])
        
        if current_ema is None:
            raise HTTPException(status_code=400, detail=f"Insufficient data for EMA calculation. Need at least {period} data points.")
        
        # Calculate price position relative to EMA
        price_diff = current_price - current_ema
        price_diff_pct = (price_diff / current_ema) * 100
        
        # Generate signal based on price vs EMA
        if price_diff_pct > 2:
            ema_signal = "BUY"
            interpretation = "Price above EMA - Uptrend"
        elif price_diff_pct < -2:
            ema_signal = "SELL"
            interpretation = "Price below EMA - Downtrend"
        else:
            ema_signal = "HOLD"
            interpretation = "Price near EMA - Consolidation"
        
        confidence = min(100, abs(price_diff_pct) * 10)
        
        # Build response with recent history (last 5 periods)
        recent_history = []
        for i in range(max(0, len(data) - 5), len(data)):
            date = data.index[i]
            price = float(data['Close'].iloc[i])
            ema_val = float(ema_values.iloc[i]) if not pd.isna(ema_values.iloc[i]) else None
            
            if ema_val is not None:
                recent_history.append({
                    "date": date.isoformat(),
                    "price": price,
                    "ema": round(ema_val, 2),
                    "diff": round(price - ema_val, 2),
                    "diff_pct": round((price - ema_val) / ema_val * 100, 2),
                })
        
        return {
            "ticker": ticker_upper,
            "indicator": "EMA",
            "period": period,
            "current": {
                "price": round(current_price, 2),
                "ema": round(current_ema, 2),
                "difference": round(price_diff, 2),
                "difference_pct": round(price_diff_pct, 2),
            },
            "signal": ema_signal,
            "confidence": round(confidence, 1),
            "interpretation": interpretation,
            "recent_history": recent_history,
            "data_source": "simulated" if is_simulated else "live",
            "last_updated": data.index[-1].isoformat() if not is_simulated else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating EMA for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating EMA: {str(e)}")


@router.get("/indicators/atr/{ticker}")
async def get_atr_indicator(
    ticker: str,
    period: int = Query(14, ge=2, le=50),
    lookback: int = Query(30, ge=1, le=365),
    interval: str = Query("1d", regex="^(1h|4h|1d|1wk)$"),
    db: Session = Depends(get_db)
):
    """
    Get ATR (Average True Range) for a ticker.
    
    ATR measures volatility by calculating the average of true ranges.
    Higher ATR = Higher volatility
    Lower ATR = Lower volatility
    
    Uses: Position sizing, stop-loss calculation, volatility measurement
    
    Args:
        ticker: Stock/ETF symbol
        period: ATR period (default: 14)
        lookback: Number of periods to fetch (default: 30)
        interval: Timeframe - "1h", "4h", "1d" (default), "1wk"
    
    Returns:
        Current ATR value, volatility level, and recent history
    """
    try:
        from backend.signals.indicators import ATR

        ticker_upper = ticker.upper()

        data, is_simulated = _fetch_price_data(ticker_upper, lookback, interval)

        # Calculate ATR
        atr_calc = ATR(period=period)
        atr_values = atr_calc.calculate(data['High'], data['Low'], data['Close'])
        
        # Get current ATR (last value)
        current_atr = float(atr_values.iloc[-1]) if not pd.isna(atr_values.iloc[-1]) else None
        current_price = float(data['Close'].iloc[-1])
        
        if current_atr is None:
            raise HTTPException(status_code=400, detail=f"Insufficient data for ATR calculation. Need at least {period + 1} data points.")
        
        # Calculate ATR as percentage of price
        atr_pct = (current_atr / current_price) * 100
        
        # Classify volatility
        if atr_pct < 1:
            volatility = "Very Low"
        elif atr_pct < 2:
            volatility = "Low"
        elif atr_pct < 3:
            volatility = "Normal"
        elif atr_pct < 4:
            volatility = "High"
        else:
            volatility = "Very High"
        
        # Build response with recent history (last 5 periods)
        recent_history = []
        for i in range(max(0, len(data) - 5), len(data)):
            date = data.index[i]
            price = float(data['Close'].iloc[i])
            atr_val = float(atr_values.iloc[i]) if not pd.isna(atr_values.iloc[i]) else None
            
            if atr_val is not None:
                recent_history.append({
                    "date": date.isoformat(),
                    "price": price,
                    "atr": round(atr_val, 2),
                    "atr_pct": round((atr_val / price) * 100, 2),
                })
        
        return {
            "ticker": ticker_upper,
            "indicator": "ATR",
            "period": period,
            "current": {
                "atr": round(current_atr, 2),
                "atr_pct": round(atr_pct, 2),
                "volatility": volatility,
            },
            "interpretation": f"Average True Range: {round(current_atr, 2)} ({volatility} Volatility)",
            "recent_history": recent_history,
            "data_source": "simulated" if is_simulated else "live",
            "last_updated": data.index[-1].isoformat() if not is_simulated else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating ATR for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating ATR: {str(e)}")


@router.get("/indicators/bollinger-bands/{ticker}")
async def get_bollinger_bands_indicator(
    ticker: str,
    period: int = Query(20, ge=2, le=100),
    std_dev: float = Query(2.0, ge=0.5, le=5.0),
    lookback: int = Query(30, ge=1, le=365),
    interval: str = Query("1d", regex="^(1h|4h|1d|1wk)$"),
    db: Session = Depends(get_db)
):
    """
    Get Bollinger Bands for a ticker.
    
    Bollinger Bands consist of:
    - Middle Band: SMA (Simple Moving Average)
    - Upper Band: Middle + (2 * Standard Deviation)
    - Lower Band: Middle - (2 * Standard Deviation)
    
    Uses: Support/Resistance levels, volatility measurement, mean reversion signals
    
    Args:
        ticker: Stock/ETF symbol
        period: Period for SMA (default: 20)
        std_dev: Standard deviation multiplier (default: 2.0)
        lookback: Number of periods to fetch (default: 30)
        interval: Timeframe - "1h", "4h", "1d" (default), "1wk"
    
    Returns:
        Upper, middle, and lower band values, price position, and recent history
    """
    try:
        from backend.signals.indicators import BollingerBands

        ticker_upper = ticker.upper()

        data, is_simulated = _fetch_price_data(ticker_upper, lookback, interval)

        # Calculate Bollinger Bands
        bb_calc = BollingerBands(period=period, std_dev=std_dev)
        upper, middle, lower = bb_calc.calculate(data['Close'])
        
        # Get current values (last value)
        current_price = float(data['Close'].iloc[-1])
        current_upper = float(upper.iloc[-1]) if not pd.isna(upper.iloc[-1]) else None
        current_middle = float(middle.iloc[-1]) if not pd.isna(middle.iloc[-1]) else None
        current_lower = float(lower.iloc[-1]) if not pd.isna(lower.iloc[-1]) else None
        
        if current_upper is None or current_middle is None or current_lower is None:
            raise HTTPException(status_code=400, detail=f"Insufficient data for Bollinger Bands. Need at least {period} data points.")
        
        # Determine price position
        bb_range = current_upper - current_lower
        price_position = (current_price - current_lower) / bb_range
        
        if price_position > 0.8:
            position = "Near Upper Band"
            bb_signal = "Overbought"
        elif price_position < 0.2:
            position = "Near Lower Band"
            bb_signal = "Oversold"
        elif price_position > 0.5:
            position = "Above Middle"
            bb_signal = "Bullish"
        else:
            position = "Below Middle"
            bb_signal = "Bearish"
        
        # Build response with recent history (last 5 periods)
        recent_history = []
        for i in range(max(0, len(data) - 5), len(data)):
            date = data.index[i]
            price = float(data['Close'].iloc[i])
            upper_val = float(upper.iloc[i]) if not pd.isna(upper.iloc[i]) else None
            middle_val = float(middle.iloc[i]) if not pd.isna(middle.iloc[i]) else None
            lower_val = float(lower.iloc[i]) if not pd.isna(lower.iloc[i]) else None
            
            if upper_val is not None and middle_val is not None and lower_val is not None:
                recent_history.append({
                    "date": date.isoformat(),
                    "price": price,
                    "upper": round(upper_val, 2),
                    "middle": round(middle_val, 2),
                    "lower": round(lower_val, 2),
                })
        
        return {
            "ticker": ticker_upper,
            "indicator": "BollingerBands",
            "parameters": {
                "period": period,
                "std_dev": std_dev,
            },
            "current": {
                "price": round(current_price, 2),
                "upper": round(current_upper, 2),
                "middle": round(current_middle, 2),
                "lower": round(current_lower, 2),
                "position": position,
                "position_pct": round(price_position * 100, 1),
            },
            "signal": bb_signal,
            "interpretation": f"Price {position}: {bb_signal}",
            "recent_history": recent_history,
            "data_source": "simulated" if is_simulated else "live",
            "last_updated": data.index[-1].isoformat() if not is_simulated else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating Bollinger Bands for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating Bollinger Bands: {str(e)}")


@router.get("/indicators/composite-signal/{ticker}")
async def get_composite_signal(
    ticker: str,
    lookback: int = Query(30, ge=1, le=365),
    interval: str = Query("1d", regex="^(1h|4h|1d|1wk)$"),
    db: Session = Depends(get_db)
):
    """
    Get composite trading signal combining all 5 technical indicators.
    
    This endpoint uses a voting system where each indicator "votes" for BUY, SELL, or HOLD.
    The final signal is determined by majority vote with confidence based on indicator agreement.
    
    Indicators included:
    - RSI (14-period): Momentum
    - MACD (12/26/9): Trend momentum
    - EMA (20-period): Trend identification
    - Bollinger Bands (20/2.0): Support/Resistance
    - ATR (14-period): Volatility (influences confidence)
    
    Args:
        ticker: Stock/ETF symbol
        lookback: Number of periods to fetch (default: 30)
        interval: Timeframe - "1h", "4h", "1d" (default), "1wk"
    
    Returns:
        Composite signal (BUY/SELL/HOLD), confidence, component breakdown, and voting results
    """
    try:
        from backend.signals.indicators import SignalGenerator

        ticker_upper = ticker.upper()

        data, is_simulated = _fetch_price_data(ticker_upper, lookback, interval)

        # Generate composite signal
        signal_gen = SignalGenerator()
        signal = signal_gen.generate_signal(data)
        
        # Handle insufficient data error
        if 'error' in signal:
            raise HTTPException(status_code=400, detail=signal['error'])
        
        return {
            "ticker": ticker_upper,
            "signal": signal['signal'],
            "confidence": signal['confidence'],
            "interval": interval,
            "voting": {
                "buy_votes": signal['votes']['BUY'],
                "sell_votes": signal['votes']['SELL'],
                "hold_votes": signal['votes']['HOLD'],
                "total_indicators": 4,
            },
            "components": {
                "rsi": {
                    "value": signal['components']['rsi']['value'],
                    "signal": signal['components']['rsi']['signal'],
                    "confidence": signal['components']['rsi']['confidence'],
                },
                "macd": {
                    "value": signal['components']['macd']['value'],
                    "signal": signal['components']['macd']['signal'],
                    "confidence": signal['components']['macd']['confidence'],
                },
                "ema": {
                    "value": signal['components']['ema']['value'],
                    "signal": signal['components']['ema']['signal'],
                    "confidence": signal['components']['ema']['confidence'],
                },
                "bollinger_bands": {
                    "value": signal['components']['bb']['value'],
                    "signal": signal['components']['bb']['signal'],
                    "confidence": signal['components']['bb']['confidence'],
                },
                "atr": {
                    "value": signal['components']['atr']['value'],
                    "atr_pct": signal['components']['atr']['atr_pct'],
                    "volatility_factor": signal['components']['atr']['volatility_factor'],
                },
            },
            "interpretation": (
                "🟢 Strong BUY signal - Multiple indicators confirm uptrend momentum" 
                if signal['signal'] == 'BUY' and signal['confidence'] > 70
                else "🟢 BUY signal - Bullish indicators outweigh bearish ones"
                if signal['signal'] == 'BUY'
                else "🔴 Strong SELL signal - Multiple indicators confirm downtrend momentum"
                if signal['signal'] == 'SELL' and signal['confidence'] > 70
                else "🔴 SELL signal - Bearish indicators outweigh bullish ones"
                if signal['signal'] == 'SELL'
                else "🟡 HOLD signal - Indicators are mixed or neutral"
            ),
            "data_source": "simulated" if is_simulated else "live",
            "last_updated": data.index[-1].isoformat() if not is_simulated else None,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating composite signal for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating composite signal: {str(e)}")


@router.get("/risk/{ticker}")
async def get_risk_analysis(
    ticker: str,
    lookback: int = Query(30, ge=1, le=365),
    interval: str = Query("1d", regex="^(1h|4h|1d|1wk)$"),
    account_balance: float = Query(100000, ge=1000, le=10000000),
    risk_per_trade: float = Query(0.02, ge=0.001, le=0.10),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive risk analysis and trade planning for a ticker.
    
    Combines composite signal with risk management to generate complete trade plans
    including position sizing, stop-loss, take-profit, and portfolio allocation.
    
    Uses:
    - Signal confidence to adjust position size
    - ATR volatility for dynamic exit levels
    - Kelly Criterion (simplified) for position sizing
    - Risk-reward ratio validation (minimum 1:2)
    
    Args:
        ticker: Stock/ETF symbol
        lookback: Number of periods to fetch (default: 30)
        interval: Timeframe - "1h", "4h", "1d" (default), "1wk"
        account_balance: Account size for position calculation (default: $100k)
        risk_per_trade: % of account to risk per trade (default: 2%)
    
    Returns:
        Complete trade plan with position sizing, exits, and validation
    """
    try:
        from backend.signals.indicators import SignalGenerator

        ticker_upper = ticker.upper()

        data, is_simulated = _fetch_price_data(ticker_upper, lookback, interval)

        if len(data) < 14:
            raise HTTPException(status_code=400, detail="Insufficient data for analysis (need min 14 periods)")
        
        # Get current price and ATR
        current_price = float(data['Close'].iloc[-1])
        
        # Calculate ATR for exit levels
        from backend.signals.indicators import ATR
        atr_calculator = ATR(period=14)
        atr_values = atr_calculator.calculate(data['High'], data['Low'], data['Close'])
        current_atr = float(atr_values.iloc[-1])
        
        # Generate composite signal
        signal_gen = SignalGenerator()
        signal = signal_gen.generate_signal(data)
        
        if 'error' in signal:
            raise HTTPException(status_code=400, detail=signal['error'])
        
        # Initialize Risk Engine
        engine = RiskEngine(
            account_balance=account_balance,
            risk_per_trade=risk_per_trade,
            max_position_size=0.10,
            sl_atr_multiple=2.0,
            tp_atr_multiple=3.0,
            min_reward_ratio=2.0,
            max_open_positions=5
        )
        
        # Generate full trade plan
        trade_plan = engine.calculate_full_trade_plan(
            entry_price=current_price,
            signal_confidence=signal['confidence'],
            atr=current_atr,
            signal=signal['signal'],
            ticker=ticker_upper
        )
        
        # Portfolio allocation recommendation
        portfolio = engine.calculate_portfolio_allocation(
            open_positions=2,  # Assume 2 open positions (conservative)
            new_signal_confidence=signal['confidence']
        )
        
        # Drawdown limits
        drawdown = engine.get_max_drawdown_limit()
        
        # Validation
        is_valid, warnings = engine.validate_trade(trade_plan)
        
        return {
            "ticker": ticker_upper,
            "timestamp": datetime.utcnow().isoformat(),
            "data_source": "simulated" if is_simulated else "live",
            "last_updated": data.index[-1].isoformat() if not is_simulated else None,
            "interval": interval,
            "market_data": {
                "current_price": round(current_price, 4),
                "atr": round(current_atr, 4),
                "atr_pct": round((current_atr / current_price) * 100, 2),
            },
            "signal": {
                "type": signal['signal'],
                "confidence": signal['confidence'],
                "interpretation": (
                    "🟢 Strong BUY" if signal['signal'] == 'BUY' and signal['confidence'] > 70
                    else "🟢 BUY" if signal['signal'] == 'BUY'
                    else "🔴 Strong SELL" if signal['signal'] == 'SELL' and signal['confidence'] > 70
                    else "🔴 SELL" if signal['signal'] == 'SELL'
                    else "🟡 HOLD"
                ),
            },
            "trade_plan": {
                "entry_price": trade_plan["entry_price"],
                "signal": trade_plan["signal"],
                "position": {
                    "size": trade_plan["position"]["size"],
                    "value": trade_plan["position"]["value"],
                    "risk_amount": trade_plan["position"]["risk_amount"],
                    "risk_percentage": trade_plan["position"]["risk_percentage"],
                },
                "exits": {
                    "stop_loss": trade_plan["exits"].get("stop_loss"),
                    "take_profit": trade_plan["exits"].get("take_profit"),
                    "risk_per_share": trade_plan["exits"].get("risk_per_share", 0),
                    "reward_per_share": trade_plan["exits"].get("reward_per_share", 0),
                    "risk_reward_ratio": trade_plan["exits"].get("risk_reward_ratio", 0),
                },
                "metrics": {
                    "potential_loss": trade_plan["metrics"]["potential_loss"],
                    "potential_gain": trade_plan["metrics"]["potential_gain"],
                    "expected_value": trade_plan["metrics"]["expected_value"],
                },
                "portfolio_exposure": trade_plan.get("portfolio_exposure") or {},
                "exposure_adjustment": trade_plan.get("exposure_adjustment") or {},
            },
            "portfolio": {
                "can_open_new_position": portfolio["can_open_new_position"],
                "open_positions": portfolio["open_positions"],
                "max_positions": portfolio["max_positions"],
                "slots_available": portfolio["slots_available"],
                "remaining_cash": portfolio["remaining_cash"],
            },
            "account_protection": {
                "daily_loss_limit": drawdown["daily_loss_limit"],
                "weekly_loss_limit": drawdown["weekly_loss_limit"],
                "monthly_loss_limit": drawdown["monthly_loss_limit"],
                "account_stop_loss": drawdown["account_stop_loss"],
            },
            "validation": {
                "is_valid": is_valid,
                "warnings": warnings,
                "recommendation": (
                    "✅ READY TO TRADE" if is_valid and trade_plan["signal"] != "HOLD"
                    else "⚠️ HOLD - High risk-reward ratio" if is_valid and trade_plan["signal"] == "HOLD"
                    else "❌ NOT READY - Address warnings before trading"
                ),
            },
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating risk analysis for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating risk analysis: {str(e)}")


# ============================================================================
# Signal Endpoints
# ============================================================================

@router.get("/signals", response_model=List[SignalResponse])
async def list_signals(
    is_active: bool = True,
    signal_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List active signals"""
    query = db.query(Signal).filter(Signal.is_active == is_active)
    
    if signal_type:
        query = query.filter(Signal.signal_type == signal_type)
    
    signals = query.order_by(Signal.generated_at.desc()).offset(skip).limit(limit).all()
    return signals


@router.get("/stats")
async def get_market_stats(db: Session = Depends(get_db)):
    """Get market data statistics"""
    stocks_count = db.query(Stock).count()
    candles_count = db.query(Candle).count()
    watchlists_count = db.query(Watchlist).count()
    signals_count = db.query(Signal).filter(Signal.is_active == True).count()
    
    cache_stats = get_fetcher().get_cache_stats()
    
    return {
        "stocks_in_db": stocks_count,
        "candles_in_db": candles_count,
        "watchlists": watchlists_count,
        "active_signals": signals_count,
        "cache": cache_stats,
    }
