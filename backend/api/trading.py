"""
Trading API Routes - Manual Trade Approval System

REST Endpoints for trading operations:
- GET  /api/trading/signals       - Get pending signals
- POST /api/trading/signals       - Generate new signal
- POST /api/trading/approve       - Approve a signal
- POST /api/trading/reject        - Reject a signal
- POST /api/trading/execute       - Execute approved trade
- POST /api/trading/close         - Close open trade
- GET  /api/trading/trades/open   - Get open trades
- GET  /api/trading/trades/history - Get closed trades
- GET  /api/trading/stats         - Get performance stats
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import logging
from backend.config import settings
from backend.trading.trade_manager import TradeManager, SignalType
from backend.market_data.data_fetcher import get_fetcher
from backend.signals.indicators import SignalGenerator, RSI

router = APIRouter(prefix="/api/trading", tags=["Trading"])
logger = logging.getLogger(__name__)

# Global trade manager instance
trade_manager = TradeManager()

AUTO_SIGNAL_PREFIX = "Auto-generated from Monitor:"


# ============================================================================
# Request/Response Models
# ============================================================================

class SignalRequest(BaseModel):
    """Request to generate a new trading signal"""
    symbol: str
    signal_type: str  # "BUY", "SELL", "EXIT"
    price: float
    confidence: float
    reason: str
    position_size: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    atr: Optional[float] = None


class ApprovalRequest(BaseModel):
    """Request to approve a signal"""
    signal_id: str
    approval_notes: str = ""
    modified_position_size: Optional[float] = None
    modified_stop_loss: Optional[float] = None
    modified_take_profit: Optional[float] = None


class ExecutionRequest(BaseModel):
    """Request to execute an approved trade"""
    signal_id: str


class ManualTradeRequest(BaseModel):
    """Request to open a manual trade directly (no signal/approval flow)"""
    symbol: str
    signal_type: str  # "BUY" or "SELL"
    entry_price: float
    position_size: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: str = "Manual entry"


class CloseTradeRequest(BaseModel):
    """Request to close an open trade"""
    trade_id: str
    exit_price: float
    exit_reason: str = "Manual close"


class RejectRequest(BaseModel):
    """Request to reject a signal"""
    signal_id: str
    reason: str = ""


class SignalResponse(BaseModel):
    """Trading signal response"""
    signal_id: str
    symbol: str
    type: str
    price: float
    confidence: float
    reason: str
    generated_at: str
    position_size: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    atr: Optional[float]


class TradeResponse(BaseModel):
    """Trade record response"""
    trade_id: str
    symbol: str
    entry_price: float
    entry_date: str
    position_size: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    status: str
    exit_price: Optional[float]
    exit_date: Optional[str]
    exit_reason: Optional[str]
    pnl: Optional[float]
    pnl_percent: Optional[float]
    notes: str


class StatsResponse(BaseModel):
    """Performance statistics response"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_pnl: float
    best_trade: Optional[float]
    worst_trade: Optional[float]
    total_exposure: float
    current_cash: float


class MonitoredTickersRequest(BaseModel):
    """Request payload to replace monitored tickers"""
    tickers: List[str]


class MonitoredTickersResponse(BaseModel):
    """Monitored ticker list response"""
    tickers: List[str]


class TickerQuoteResponse(BaseModel):
    """Price quote with data freshness context"""
    symbol: str
    price: Optional[float]
    source: str
    data_provider: str
    market_open: bool
    message: str
    last_updated: Optional[str]


class TickerMonitorItem(BaseModel):
    """Monitoring status for a single ticker"""
    symbol: str
    signal: str
    confidence: float
    condition: str
    action: str
    price: Optional[float]
    price_source: str
    data_provider: str
    market_open: bool
    price_message: str
    last_updated: Optional[str]
    signal_metrics: List[dict] = Field(default_factory=list)
    suggested_stop_loss: Optional[float] = None
    suggested_take_profit: Optional[float] = None


class HistoricalBar(BaseModel):
    """Single historical OHLCV bar"""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float]


class TickerHistoryResponse(BaseModel):
    """Historical data for a ticker"""
    symbol: str
    interval: str
    bars: List[HistoricalBar]
    source: str


def _normalize_ohlcv_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Normalize OHLCV column names to title case for indicator engines."""
    renamed = data.copy()
    rename_map = {
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "volume": "Volume",
    }
    renamed.columns = [rename_map.get(str(col).lower(), str(col)) for col in renamed.columns]
    return renamed


def _calculate_rsi_timeframe(
    fetcher,
    ticker: str,
    period: str,
    interval: str,
    resample_rule: Optional[str] = None,
) -> Optional[float]:
    """Calculate RSI(14) for a specific timeframe."""
    data = fetcher.get_historical_data(ticker, period=period, interval=interval, use_cache=True)
    if data is None or data.empty:
        return None

    normalized = _normalize_ohlcv_columns(data)
    if "Close" not in normalized.columns:
        return None

    close = normalized["Close"].copy()
    close.index = pd.to_datetime(close.index, utc=True)
    close = close.sort_index()

    if resample_rule:
        close = close.resample(resample_rule).last().dropna()

    if len(close) < 15:
        return None

    rsi_values = RSI(period=14).calculate(close)
    rsi_values = rsi_values.dropna()
    if rsi_values.empty:
        return None

    return float(round(float(rsi_values.iloc[-1]), 2))


def _is_regular_us_session_open() -> bool:
    """Best-effort market open check for NYSE/Nasdaq regular session."""
    now_et = datetime.now(ZoneInfo("America/New_York"))
    if now_et.weekday() >= 5:
        return False
    minutes = now_et.hour * 60 + now_et.minute
    return (9 * 60 + 30) <= minutes <= (16 * 60)


def _build_quote(symbol: str) -> dict:
    """Build quote details with live/latest status and market session message."""
    ticker = symbol.upper()
    fetcher = get_fetcher()

    market_open = _is_regular_us_session_open()
    provider_mode = str(getattr(settings, "market_data_provider", "questrade") or "questrade").lower()

    # Fetch latest historical first so we can always prefer end-of-day values when market is closed.
    data = fetcher.get_historical_data(ticker, period="7d", interval="1d", use_cache=True)

    latest_close = None
    last_updated = None
    if data is not None and not data.empty:
        normalized = _normalize_ohlcv_columns(data)
        close_col = "Close" if "Close" in normalized.columns else None
        if close_col:
            latest_close = float(normalized[close_col].iloc[-1])
            idx_value = normalized.index[-1]
            ts = pd.to_datetime(idx_value, errors="coerce", utc=True)
            if pd.isna(ts):
                last_updated = str(idx_value)
            else:
                last_updated = ts.isoformat()

    if not market_open and latest_close is not None:
        return {
            "symbol": ticker,
            "price": latest_close,
            "source": "latest_close",
            "data_provider": "yahoo" if provider_mode == "yahoo" else provider_mode,
            "market_open": False,
            "message": "Market closed — showing latest close (EOD)",
            "last_updated": last_updated,
        }

    # Try to get live Questrade data with timestamp only during market hours.
    if market_open:
        live_quote = fetcher.get_price_with_timestamp(ticker)
        if live_quote:
            return {
                "symbol": ticker,
                "price": float(live_quote["price"]),
                "source": "live",
                "data_provider": str(live_quote.get("provider") or "questrade"),
                "market_open": True,
                "message": "Live intraday price",
                "last_updated": live_quote.get("timestamp"),
            }

    # Fallback to current price
    current_price = fetcher.get_current_price(ticker)

    if market_open and current_price is not None:
        return {
            "symbol": ticker,
            "price": float(current_price),
            "source": "live",
            "data_provider": "yahoo" if provider_mode == "yahoo" else provider_mode,
            "market_open": True,
            "message": "Live intraday price",
            "last_updated": datetime.utcnow().isoformat(),
        }

    if latest_close is not None:
        return {
            "symbol": ticker,
            "price": latest_close,
            "source": "latest_close",
            "data_provider": "yahoo" if provider_mode == "yahoo" else provider_mode,
            "market_open": market_open,
            "message": "Market closed — showing latest close" if not market_open else "Using latest available close",
            "last_updated": last_updated,
        }

    if current_price is not None:
        return {
            "symbol": ticker,
            "price": float(current_price),
            "source": "latest",
            "data_provider": "yahoo" if provider_mode == "yahoo" else provider_mode,
            "market_open": market_open,
            "message": "Using latest available price",
            "last_updated": None,
        }

    return {
        "symbol": ticker,
        "price": None,
        "source": "unavailable",
        "data_provider": "none",
        "market_open": market_open,
        "message": "Price data unavailable",
        "last_updated": None,
    }


def _condition_and_action(signal: str, confidence: float) -> tuple[str, str]:
    """Map indicator signal to a human-friendly condition and action."""
    if signal == "BUY":
        if confidence >= 70:
            return "Bullish momentum", "Consider opening or adding to a long position"
        return "Mildly bullish", "Watch for confirmation before entry"
    if signal == "SELL":
        if confidence >= 70:
            return "Bearish pressure", "Consider reducing risk or exiting longs"
        return "Mildly bearish", "Protect downside and wait for confirmation"
    return "Mixed / neutral", "Hold and wait"


def _build_auto_signal_reason(item: dict) -> str:
    """Build a concise analysis reason for monitor-derived signals."""
    symbol = str(item.get("symbol") or "").upper()
    condition = str(item.get("condition") or "Composite signal triggered")
    confidence = float(item.get("confidence") or 0.0)
    metrics = item.get("signal_metrics") or []

    rsi_daily = None
    macd_hist = None
    for metric in metrics:
        name = str(metric.get("name") or "")
        if name == "RSI (Daily)":
            rsi_daily = metric.get("current")
        elif name == "MACD Histogram":
            macd_hist = metric.get("current")

    parts = [f"{AUTO_SIGNAL_PREFIX} {symbol} {condition} ({confidence:.0f}% confidence)"]
    if rsi_daily is not None:
        parts.append(f"RSI={float(rsi_daily):.1f}")
    if macd_hist is not None:
        parts.append(f"MACD_hist={float(macd_hist):.4f}")
    parts.append("Composite RSI/MACD monitor trigger.")
    return " | ".join(parts)


def _build_risk_levels(signal_type: str, price: float) -> tuple[float, float]:
    """Generate default SL/TP for monitor-derived signals."""
    if signal_type == "BUY":
        return round(price * 0.98, 2), round(price * 1.04, 2)
    return round(price * 1.02, 2), round(price * 0.96, 2)


def _sync_pending_signals_from_monitor(overview: List[dict]) -> None:
    """Ensure BUY/SELL monitor statuses are represented as pending signals."""
    allowed = set(trade_manager.get_monitored_tickers())
    if not allowed:
        return

    desired: dict[str, dict] = {}
    for item in overview:
        symbol = str(item.get("symbol") or "").upper()
        signal = str(item.get("signal") or "HOLD").upper()
        price = item.get("price")
        if symbol in allowed and signal in {"BUY", "SELL"} and price is not None:
            desired[symbol] = item

    # Remove stale/invalid auto-generated monitor signals.
    for existing in list(trade_manager.pending_signals):
        if existing.symbol not in allowed:
            continue
        if not str(existing.reason or "").startswith(AUTO_SIGNAL_PREFIX):
            continue
        current = desired.get(existing.symbol)
        if current is None or existing.signal_type.value != str(current.get("signal", "")).upper():
            trade_manager.pending_signals.remove(existing)

    auto_by_symbol = {
        s.symbol: s
        for s in trade_manager.pending_signals
        if s.symbol in allowed and str(s.reason or "").startswith(AUTO_SIGNAL_PREFIX)
    }

    for symbol, item in desired.items():
        signal_type = str(item.get("signal") or "BUY").upper()
        price = float(item.get("price") or 0.0)
        confidence = max(0.0, min(100.0, float(item.get("confidence") or 0.0)))
        reason = _build_auto_signal_reason(item)
        stop_loss, take_profit = _build_risk_levels(signal_type, price)

        existing = auto_by_symbol.get(symbol)
        if existing:
            existing.price = price
            existing.confidence = confidence
            existing.reason = reason
            existing.generated_at = datetime.now()
            existing.position_size = 100
            existing.stop_loss = stop_loss
            existing.take_profit = take_profit
            continue

        trade_manager.add_signal(
            symbol=symbol,
            signal_type=SignalType(signal_type),
            price=price,
            confidence=confidence,
            reason=reason,
            position_size=100,
            stop_loss=stop_loss,
            take_profit=take_profit,
            atr=None,
        )


# ============================================================================
# Signal Endpoints
# ============================================================================

@router.get("/signals", response_model=List[SignalResponse])
def get_pending_signals():
    """
    Get all pending signals awaiting user confirmation
    
    Returns list of signals with details (price, confidence, reason, etc.)
    """
    # Sync monitor BUY/SELL statuses into pending signals so review/analysis are populated.
    # Never fail the whole endpoint if monitor sync throws.
    try:
        overview = get_monitor_overview()
        _sync_pending_signals_from_monitor(overview)
    except Exception as exc:
        logger.exception("Signal sync from monitor failed; returning existing pending signals: %s", exc)

    signals = trade_manager.get_pending_signals()
    allowed = set(trade_manager.get_monitored_tickers())
    if not allowed:
        return []
    signals = [s for s in signals if s.get("symbol") in allowed]
    return signals


@router.post("/signals", response_model=SignalResponse)
def create_signal(request: SignalRequest):
    """
    Generate a new trading signal
    
    This creates a suggestion that the user can approve or reject.
    NO trade executes until user approval.
    """
    try:
        allowed = set(trade_manager.get_monitored_tickers())
        symbol = request.symbol.upper()
        if not allowed:
            raise HTTPException(
                status_code=400,
                detail="No monitored tickers configured. Add tickers in Monitor tab first."
            )
        if symbol not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"{symbol} is not in monitored tickers. Update your monitored list first."
            )

        signal = trade_manager.add_signal(
            symbol=symbol,
            signal_type=SignalType(request.signal_type),
            price=request.price,
            confidence=request.confidence,
            reason=request.reason,
            position_size=request.position_size,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            atr=request.atr
        )
        
        return trade_manager._signal_to_dict(signal)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/monitor/tickers", response_model=MonitoredTickersResponse)
def get_monitored_tickers():
    """Get current user-defined monitored tickers."""
    return {"tickers": trade_manager.get_monitored_tickers()}


@router.put("/monitor/tickers", response_model=MonitoredTickersResponse)
def set_monitored_tickers(request: MonitoredTickersRequest):
    """Replace monitored tickers with user-provided set."""
    tickers = trade_manager.set_monitored_tickers(request.tickers)
    return {"tickers": tickers}


@router.get("/quote/{symbol}", response_model=TickerQuoteResponse)
def get_ticker_quote(symbol: str):
    """Get quote with live/latest-close context (market open/closed messaging)."""
    return _build_quote(symbol)


@router.get("/monitor/overview", response_model=List[TickerMonitorItem])
def get_monitor_overview():
    """Get condition/action overview for all monitored tickers."""
    tickers = trade_manager.get_monitored_tickers()
    fetcher = get_fetcher()
    generator = SignalGenerator()

    overview = []
    for ticker in tickers:
        quote = _build_quote(ticker)

        signal = "HOLD"
        confidence = 0.0
        condition = "Data unavailable"
        action = "Wait for data"
        signal_metrics: List[dict] = []
        suggested_stop_loss: Optional[float] = None
        suggested_take_profit: Optional[float] = None
        has_quote_price = quote.get("price") is not None

        if has_quote_price:
            if quote.get("source") == "live":
                condition = "Live price available"
                action = "Monitoring with live quote (waiting for full indicator dataset)"
            else:
                condition = "Price available"
                action = "Monitoring with latest available price (indicator data limited)"

        data = fetcher.get_historical_data(ticker, period="3mo", interval="1d", use_cache=True)
        if data is not None and not data.empty:
            normalized = _normalize_ohlcv_columns(data)
            if all(col in normalized.columns for col in ["Open", "High", "Low", "Close", "Volume"]):
                signal_data = generator.generate_signal(normalized)
                signal = str(signal_data.get("signal", "HOLD"))
                confidence = float(signal_data.get("confidence", 0.0))
                condition, action = _condition_and_action(signal, confidence)

                components = signal_data.get("components", {}) or {}
                rsi_value = (components.get("rsi", {}) or {}).get("value")
                macd_hist = (components.get("macd", {}) or {}).get("value")
                ema_value = (components.get("ema", {}) or {}).get("value")
                bb_position = (components.get("bb", {}) or {}).get("value")
                current_close = float(normalized["Close"].iloc[-1]) if not normalized.empty else None

                rsi_4h = _calculate_rsi_timeframe(
                    fetcher,
                    ticker,
                    period="1mo",
                    interval="60m",
                    resample_rule="4h",
                )
                rsi_daily = _calculate_rsi_timeframe(
                    fetcher,
                    ticker,
                    period="3mo",
                    interval="1d",
                )
                rsi_weekly = _calculate_rsi_timeframe(
                    fetcher,
                    ticker,
                    period="2y",
                    interval="1wk",
                )

                ema_diff_pct = None
                if current_close is not None and ema_value not in (None, 0):
                    ema_diff_pct = round(((current_close - float(ema_value)) / float(ema_value)) * 100, 2)

                signal_metrics = [
                    {
                        "name": "RSI (4H)",
                        "current": rsi_4h,
                        "low_trigger": 30.0,
                        "high_trigger": 70.0,
                        "unit": "index",
                        "description": "BUY below 30, SELL above 70",
                    },
                    {
                        "name": "RSI (Daily)",
                        "current": rsi_daily if rsi_daily is not None else rsi_value,
                        "low_trigger": 30.0,
                        "high_trigger": 70.0,
                        "unit": "index",
                        "description": "BUY below 30, SELL above 70",
                    },
                    {
                        "name": "RSI (Weekly)",
                        "current": rsi_weekly,
                        "low_trigger": 30.0,
                        "high_trigger": 70.0,
                        "unit": "index",
                        "description": "BUY below 30, SELL above 70",
                    },
                    {
                        "name": "RSI (Model)",
                        "current": rsi_value,
                        "low_trigger": 30.0,
                        "high_trigger": 70.0,
                        "unit": "index",
                        "description": "RSI used by current composite signal",
                    },
                    {
                        "name": "MACD Histogram",
                        "current": macd_hist,
                        "low_trigger": -0.0001,
                        "high_trigger": 0.0001,
                        "unit": "value",
                        "description": "BUY above 0, SELL below 0",
                    },
                    {
                        "name": "EMA Distance",
                        "current": ema_diff_pct,
                        "low_trigger": -2.0,
                        "high_trigger": 2.0,
                        "unit": "%",
                        "description": "BUY above +2%, SELL below -2%",
                    },
                    {
                        "name": "Bollinger Position",
                        "current": bb_position,
                        "low_trigger": 20.0,
                        "high_trigger": 80.0,
                        "unit": "%",
                        "description": "BUY below 20%, SELL above 80%",
                    },
                ]

                base_price = quote.get("price") if quote.get("price") is not None else current_close
                if base_price is not None and signal in {"BUY", "SELL"}:
                    suggested_stop_loss, suggested_take_profit = _build_risk_levels(signal, float(base_price))

        overview.append({
            "symbol": ticker,
            "signal": signal,
            "confidence": round(confidence, 1),
            "condition": condition,
            "action": action,
            "price": quote["price"],
            "price_source": quote["source"],
            "data_provider": quote["data_provider"],
            "market_open": quote["market_open"],
            "price_message": quote["message"],
            "last_updated": quote["last_updated"],
            "signal_metrics": signal_metrics,
            "suggested_stop_loss": suggested_stop_loss,
            "suggested_take_profit": suggested_take_profit,
        })

    return overview


@router.get("/monitor/history/{symbol}", response_model=TickerHistoryResponse)
def get_monitor_history(
    symbol: str,
    interval: str = "1d",
    period: str = "6mo",
    limit: int = 120
):
    """Get historical bars for a monitored ticker (live or local cache fallback)."""
    ticker = symbol.upper()
    data = get_fetcher().get_historical_data(ticker, period=period, interval=interval, use_cache=True)
    if data is None or data.empty:
        raise HTTPException(status_code=404, detail=f"No historical data available for {ticker}")

    normalized = _normalize_ohlcv_columns(data)
    required = ["Open", "High", "Low", "Close"]
    if not all(col in normalized.columns for col in required):
        raise HTTPException(status_code=500, detail=f"Historical data for {ticker} missing OHLC fields")

    trimmed = normalized.tail(max(1, min(limit, 500)))
    bars = []
    for idx, row in trimmed.iterrows():
        ts = pd.to_datetime(idx, errors="coerce", utc=True)
        timestamp = ts.isoformat() if not pd.isna(ts) else str(idx)
        bars.append({
            "timestamp": timestamp,
            "open": float(row["Open"]),
            "high": float(row["High"]),
            "low": float(row["Low"]),
            "close": float(row["Close"]),
            "volume": float(row["Volume"]) if "Volume" in normalized.columns and pd.notna(row.get("Volume")) else None,
        })

    return {
        "symbol": ticker,
        "interval": interval,
        "bars": bars,
        "source": "live_or_cache",
    }


# ============================================================================
# Approval Endpoints
# ============================================================================

@router.post("/approve")
def approve_trade(request: ApprovalRequest):
    """
    User approves a pending signal - auto-executes the trade immediately.
    """
    try:
        trade_manager.approve_trade(
            signal_id=request.signal_id,
            approval_notes=request.approval_notes,
            modified_position_size=request.modified_position_size,
            modified_stop_loss=request.modified_stop_loss,
            modified_take_profit=request.modified_take_profit
        )
        # Auto-execute immediately after approval
        trade = trade_manager.execute_trade(request.signal_id)
        trade_manager._save_records()
        return {"status": "executed", "signal_id": request.signal_id, "trade_id": trade.trade_id}
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reject")
def reject_trade(request: RejectRequest):
    """
    User rejects a pending signal
    
    Trade will not execute. Signal is discarded.
    """
    try:
        trade_manager.reject_trade(
            signal_id=request.signal_id,
            reason=request.reason
        )
        trade_manager._save_records()
        return {
            "status": "rejected",
            "signal_id": request.signal_id,
            "reason": request.reason
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Execution Endpoints
# ============================================================================

@router.post("/execute", response_model=TradeResponse)
def execute_trade(request: ExecutionRequest):
    """
    Execute an approved trade
    
    Trade must be approved first via /approve endpoint.
    This opens the position and starts tracking.
    """
    try:
        trade = trade_manager.execute_trade(request.signal_id)
        return trade_manager._trade_to_dict(trade)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/manual", response_model=TradeResponse)
def open_manual_trade(request: ManualTradeRequest):
    """
    Open a manual trade directly — no signal or approval required.
    
    Use this for record-keeping of trades you entered independently at your broker.
    """
    try:
        trade = trade_manager.manual_trade(
            symbol=request.symbol,
            signal_type=SignalType(request.signal_type),
            entry_price=request.entry_price,
            position_size=request.position_size,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            notes=request.notes
        )
        return trade_manager._trade_to_dict(trade)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/close", response_model=TradeResponse)
def close_trade(request: CloseTradeRequest):
    """
    Close an open trade
    
    Closes position at specified exit price.
    Calculates P&L and records the trade.
    """
    try:
        trade = trade_manager.close_trade(
            trade_id=request.trade_id,
            exit_price=request.exit_price,
            exit_reason=request.exit_reason
        )
        
        return trade_manager._trade_to_dict(trade)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Monitoring Endpoints
# ============================================================================

@router.get("/trades/open", response_model=List[TradeResponse])
def get_open_trades():
    """
    Get all open (active) trades
    
    Returns list of trades currently being monitored.
    """
    trades = trade_manager.get_open_trades()
    return trades


@router.get("/trades/history", response_model=List[TradeResponse])
def get_trade_history():
    """
    Get trade history (closed trades)
    
    Returns list of all closed trades with P&L information.
    """
    history = trade_manager.get_trade_history()
    return history


@router.delete("/trades/history/{trade_id}")
def delete_trade_history_entry(trade_id: str):
    """Delete a closed trade from history."""
    try:
        trade_manager.delete_trade_history_entry(trade_id)
        return {"message": "Trade deleted successfully", "trade_id": trade_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
def get_performance_stats():
    """
    Get performance statistics
    
    Returns summary statistics: win rate, total P&L, best/worst trades, etc.
    """
    stats = trade_manager.get_performance_stats()
    return stats


# ============================================================================
# Summary Endpoints
# ============================================================================

@router.get("/dashboard")
def get_dashboard():
    """
    Get complete trading dashboard
    
    Returns: pending signals, open trades, closed trades, stats
    """
    return {
        "pending_signals": trade_manager.get_pending_signals(),
        "open_trades": trade_manager.get_open_trades(),
        "trade_history": trade_manager.get_trade_history(),
        "performance": trade_manager.get_performance_stats(),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/status")
def get_status():
    """
    Get current system status
    
    Returns counts of pending signals, open trades, closed trades.
    """
    pending = len(trade_manager.get_pending_signals())
    open_trades = len(trade_manager.get_open_trades())
    closed_trades = len(trade_manager.get_trade_history())
    
    return {
        "status": "running",
        "pending_signals": pending,
        "open_trades": open_trades,
        "closed_trades": closed_trades,
        "total_trades": closed_trades,
        "timestamp": datetime.now().isoformat()
    }
