"""
Backtesting Engine - Phase 4

Simulates trading strategies on historical data to validate performance.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade"""
    ticker: str
    entry_date: datetime
    entry_price: float
    entry_signal: str  # BUY or SELL
    entry_confidence: float
    position_size: int
    position_value: float
    exit_date: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    duration_days: Optional[int] = None

    def close_trade(self, exit_date: datetime, exit_price: float, reason: str):
        """Close the trade and calculate P&L"""
        self.exit_date = exit_date
        self.exit_price = exit_price
        self.exit_reason = reason
        self.duration_days = (exit_date - self.entry_date).days
        
        if self.entry_signal == "BUY":
            self.pnl = (exit_price - self.entry_price) * self.position_size
        else:  # SELL
            self.pnl = (self.entry_price - exit_price) * self.position_size
        
        self.pnl_percent = (self.pnl / self.position_value) * 100


@dataclass
@dataclass
class PortfolioSnapshot:
    """Portfolio state at a specific point in time"""
    date: datetime
    cash: float
    open_positions_value: float
    closed_trades_value: float
    total_value: float
    open_position_count: int
    closed_trade_count: int


class BacktestEngine:
    """Main backtesting engine"""
    
    def __init__(
        self,
        initial_capital: float = 100000,
        max_portfolio_exposure: float = 0.50,
        max_position_size: float = 0.10,
        max_open_positions: int = 5,
        risk_per_trade: float = 0.02,
        commission_percent: float = 0.001  # 0.1% per trade
    ):
        """
        Initialize backtesting engine.
        
        Args:
            initial_capital: Starting account balance
            max_portfolio_exposure: Max total deployment (%)
            max_position_size: Max position size (%)
            max_open_positions: Max concurrent positions
            risk_per_trade: Risk per trade (%)
            commission_percent: Trading commission (%)
        """
        self.initial_capital = initial_capital
        self.max_portfolio_exposure = max_portfolio_exposure
        self.max_position_size = max_position_size
        self.max_open_positions = max_open_positions
        self.risk_per_trade = risk_per_trade
        self.commission_percent = commission_percent
        
        # State tracking
        self.cash = initial_capital
        self.open_trades: Dict[str, Trade] = {}
        self.closed_trades: List[Trade] = []
        self.portfolio_history: List[PortfolioSnapshot] = []
        self.daily_returns: List[float] = []
        
    def calculate_position_size(
        self,
        entry_price: float,
        atr: float,
        confidence: float = 75.0,
        account_value: Optional[float] = None
    ) -> int:
        """Calculate position size based on risk parameters"""
        if account_value is None:
            account_value = self.get_portfolio_value()
        
        # Kelly criterion with confidence adjustment
        risk_amount = account_value * self.risk_per_trade
        stop_loss_distance = atr * 2  # 2 ATR stops
        base_position = int(risk_amount / stop_loss_distance)
        
        # Adjust for confidence
        confidence_factor = confidence / 100.0
        position_size = int(base_position * confidence_factor)
        
        # Limit by max position size
        max_position_value = account_value * self.max_position_size
        max_position = int(max_position_value / entry_price)
        
        return min(position_size, max_position)
    
    def get_portfolio_value(self) -> float:
        """Calculate current total portfolio value"""
        open_value = sum(t.position_value for t in self.open_trades.values())
        closed_value = sum(t.pnl for t in self.closed_trades if t.pnl)
        return self.cash + open_value + (closed_value or 0)
    
    def get_open_positions_value(self) -> float:
        """Get total value of open positions"""
        return sum(t.position_value for t in self.open_trades.values())
    
    def can_open_position(self, position_value: float) -> Tuple[bool, str]:
        """Check if new position can be opened"""
        # Check position count
        if len(self.open_trades) >= self.max_open_positions:
            return False, "Max open positions reached"
        
        # Check portfolio exposure
        current_exposure = self.get_open_positions_value()
        max_exposure = self.get_portfolio_value() * self.max_portfolio_exposure
        
        if current_exposure + position_value > max_exposure:
            return False, "Portfolio exposure limit exceeded"
        
        # Check cash
        commission = position_value * self.commission_percent
        if self.cash < commission:
            return False, "Insufficient cash for commission"
        
        return True, "OK"
    
    def open_trade(
        self,
        ticker: str,
        date: datetime,
        entry_price: float,
        signal: str,
        confidence: float,
        atr: float
    ) -> Optional[Trade]:
        """Open a new trade"""
        if ticker in self.open_trades:
            return None  # Already have position
        
        # Calculate position size
        position_size = self.calculate_position_size(entry_price, atr, confidence)
        if position_size <= 0:
            return None
        
        position_value = position_size * entry_price
        
        # Check if we can open
        can_open, reason = self.can_open_position(position_value)
        if not can_open:
            logger.info(f"Cannot open {ticker}: {reason}")
            return None
        
        # Create trade
        trade = Trade(
            ticker=ticker,
            entry_date=date,
            entry_price=entry_price,
            entry_signal=signal,
            entry_confidence=confidence,
            position_size=position_size,
            position_value=position_value
        )
        
        # Deduct commission
        commission = position_value * self.commission_percent
        self.cash -= commission
        
        self.open_trades[ticker] = trade
        logger.info(f"Opened {ticker}: {position_size} shares @ ${entry_price:.2f}")
        return trade
    
    def close_trade(
        self,
        ticker: str,
        date: datetime,
        exit_price: float,
        reason: str = "Signal"
    ) -> Optional[Trade]:
        """Close an open trade"""
        if ticker not in self.open_trades:
            return None
        
        trade = self.open_trades.pop(ticker)
        trade.close_trade(date, exit_price, reason)
        
        # Add P&L and commission back to cash
        self.cash += (trade.exit_price * trade.position_size)
        commission = trade.position_value * self.commission_percent
        self.cash -= commission
        
        self.closed_trades.append(trade)
        logger.info(f"Closed {ticker}: P&L ${trade.pnl:.2f} ({trade.pnl_percent:.2f}%)")
        return trade
    
    def mark_to_market(self, date: datetime, prices: Dict[str, float]):
        """Update open positions to current market prices"""
        for ticker, trade in self.open_trades.items():
            if ticker in prices:
                current_price = prices[ticker]
                trade.position_value = trade.position_size * current_price
    
    def record_snapshot(self, date: datetime):
        """Record portfolio state"""
        snapshot = PortfolioSnapshot(
            date=date,
            cash=self.cash,
            open_positions_value=self.get_open_positions_value(),
            closed_trades_value=sum(t.pnl for t in self.closed_trades if t.pnl) or 0,
            total_value=self.get_portfolio_value(),
            open_position_count=len(self.open_trades),
            closed_trade_count=len(self.closed_trades)
        )
        self.portfolio_history.append(snapshot)
    
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.closed_trades:
            return {}
        
        total_trades = len(self.closed_trades)
        winning_trades = [t for t in self.closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in self.closed_trades if t.pnl and t.pnl < 0]
        
        total_pnl = sum(t.pnl for t in self.closed_trades if t.pnl)
        total_return_pct = (total_pnl / self.initial_capital) * 100
        
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0
        
        avg_win = (sum(t.pnl for t in winning_trades) / len(winning_trades)) if winning_trades else 0
        avg_loss = (sum(t.pnl for t in losing_trades) / len(losing_trades)) if losing_trades else 0
        
        profit_factor = abs(sum(t.pnl for t in winning_trades) / sum(t.pnl for t in losing_trades)) if losing_trades else 0
        
        avg_trade_duration = (sum(t.duration_days for t in self.closed_trades if t.duration_days) / total_trades) if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate_percent": win_rate,
            "total_pnl": total_pnl,
            "total_return_percent": total_return_pct,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "avg_trade_duration_days": avg_trade_duration,
            "final_portfolio_value": self.get_portfolio_value()
        }
