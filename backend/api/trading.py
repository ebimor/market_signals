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
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from backend.trading.trade_manager import TradeManager, SignalType

router = APIRouter(prefix="/api/trading", tags=["Trading"])

# Global trade manager instance
trade_manager = TradeManager()


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


# ============================================================================
# Signal Endpoints
# ============================================================================

@router.get("/signals", response_model=List[SignalResponse])
def get_pending_signals():
    """
    Get all pending signals awaiting user confirmation
    
    Returns list of signals with details (price, confidence, reason, etc.)
    """
    signals = trade_manager.get_pending_signals()
    return signals


@router.post("/signals", response_model=SignalResponse)
def create_signal(request: SignalRequest):
    """
    Generate a new trading signal
    
    This creates a suggestion that the user can approve or reject.
    NO trade executes until user approval.
    """
    try:
        signal = trade_manager.add_signal(
            symbol=request.symbol,
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
