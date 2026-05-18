"""
Trade Management System - Manual Approval Workflow

Implements manual trade confirmation workflow:
1. Generate signal suggestion
2. User reviews and confirms
3. Trade executes (if confirmed)
4. Trade is recorded
5. Exit signals generated for confirmed trades
"""

import json
import os
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TradeStatus(str, Enum):
    """Trade lifecycle states"""
    PENDING = "pending"          # Signal generated, awaiting confirmation
    APPROVED = "approved"        # User confirmed, ready to execute
    EXECUTED = "executed"        # Trade opened
    CLOSED = "closed"            # Trade closed (take profit/stop loss)
    REJECTED = "rejected"        # User rejected


class SignalType(str, Enum):
    """Trading signal types"""
    BUY = "BUY"
    SELL = "SELL"
    EXIT = "EXIT"


@dataclass
class TradeSignal:
    """Trading signal suggestion"""
    signal_id: str                    # Unique ID
    symbol: str                       # Ticker
    signal_type: SignalType           # BUY, SELL, EXIT
    price: float                      # Entry/exit price
    confidence: float                 # Confidence 0-100
    reason: str                       # Why this signal
    generated_at: datetime            # When generated
    position_size: Optional[float] = None  # Suggested position size
    stop_loss: Optional[float] = None      # Suggested stop loss
    take_profit: Optional[float] = None    # Suggested take profit
    atr: Optional[float] = None           # Average true range


@dataclass
class ExecutedTrade:
    """Executed trade record"""
    trade_id: str                     # Unique ID
    symbol: str                       # Ticker
    signal_id: str                    # Original signal ID
    entry_price: float                # Entry price
    entry_date: datetime              # Entry date
    position_size: float              # Number of shares/contracts
    stop_loss: Optional[float] = None # Stop loss price
    take_profit: Optional[float] = None # Take profit price
    status: TradeStatus = TradeStatus.EXECUTED  # Current status
    exit_price: Optional[float] = None          # Exit price (if closed)
    exit_date: Optional[datetime] = None        # Exit date (if closed)
    exit_reason: Optional[str] = None           # Why closed
    pnl: Optional[float] = None                 # Profit/loss $
    pnl_percent: Optional[float] = None         # Profit/loss %
    notes: str = ""                             # User notes


@dataclass
class TradeApproval:
    """Trade approval request"""
    signal: TradeSignal
    approved: bool = False
    approval_time: Optional[datetime] = None
    approval_notes: str = ""
    modified_position_size: Optional[float] = None  # User can adjust
    modified_stop_loss: Optional[float] = None
    modified_take_profit: Optional[float] = None


class TradeManager:
    """
    Manage manual trade approval workflow
    
    Workflow:
    1. add_signal() - Generate signal suggestion
    2. get_pending_signals() - Show pending signals to user
    3. approve_trade() - User approves
    4. execute_trade() - Trade executes
    5. close_trade() - Trade closes
    6. get_trade_history() - View history
    """
    
    def __init__(self, records_file: str = "backend/trading/trade_records.json"):
        self.records_file = records_file
        os.makedirs(os.path.dirname(records_file), exist_ok=True)
        
        self.initial_cash = 100000.0
        self.monitored_tickers: List[str] = ["AAPL", "MSFT", "TSLA"]
        self.pending_signals: List[TradeSignal] = []
        self.pending_approvals: Dict[str, TradeApproval] = {}
        self.executed_trades: List[ExecutedTrade] = []
        
        self._load_records()
        logger.info("TradeManager initialized")
    
    # ========================================================================
    # Signal Generation
    # ========================================================================
    
    def add_signal(
        self,
        symbol: str,
        signal_type: SignalType,
        price: float,
        confidence: float,
        reason: str,
        position_size: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        atr: Optional[float] = None
    ) -> TradeSignal:
        """
        Generate a new signal suggestion for user review.
        
        Args:
            symbol: Ticker symbol
            signal_type: BUY, SELL, or EXIT
            price: Entry/exit price
            confidence: 0-100 confidence score
            reason: Why this signal (e.g., "MACD Bull + RSI 45")
            position_size: Suggested position size (shares)
            stop_loss: Suggested stop loss price
            take_profit: Suggested take profit price
            atr: Average true range for position sizing
            
        Returns:
            TradeSignal with pending status
        """
        signal_id = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        signal = TradeSignal(
            signal_id=signal_id,
            symbol=symbol,
            signal_type=signal_type,
            price=price,
            confidence=confidence,
            reason=reason,
            generated_at=datetime.now(),
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            atr=atr
        )
        
        self.pending_signals.append(signal)
        logger.info(f"✅ Signal created: {signal_id} ({symbol} {signal_type})")
        
        return signal
    
    # ========================================================================
    # User Approval
    # ========================================================================
    
    def get_pending_signals(self) -> List[Dict]:
        """Get all pending signals awaiting user confirmation"""
        return [self._signal_to_dict(s) for s in self.pending_signals]
    
    def approve_trade(
        self,
        signal_id: str,
        approval_notes: str = "",
        modified_position_size: Optional[float] = None,
        modified_stop_loss: Optional[float] = None,
        modified_take_profit: Optional[float] = None
    ) -> TradeApproval:
        """
        User approves a pending signal for execution.
        
        Args:
            signal_id: ID of signal to approve
            approval_notes: Optional notes from user
            modified_position_size: User can adjust suggested size
            modified_stop_loss: User can adjust suggested SL
            modified_take_profit: User can adjust suggested TP
            
        Returns:
            TradeApproval record
        """
        signal = next((s for s in self.pending_signals if s.signal_id == signal_id), None)
        if not signal:
            raise ValueError(f"Signal not found: {signal_id}")
        
        approval = TradeApproval(
            signal=signal,
            approved=True,
            approval_time=datetime.now(),
            approval_notes=approval_notes,
            modified_position_size=modified_position_size,
            modified_stop_loss=modified_stop_loss,
            modified_take_profit=modified_take_profit
        )
        
        self.pending_approvals[signal_id] = approval
        logger.info(f"✅ Trade approved: {signal_id}")
        
        return approval
    
    def reject_trade(self, signal_id: str, reason: str = "") -> None:
        """User rejects a pending signal"""
        signal = next((s for s in self.pending_signals if s.signal_id == signal_id), None)
        if signal:
            self.pending_signals.remove(signal)
            logger.info(f"❌ Trade rejected: {signal_id} - {reason}")
    
    # ========================================================================
    # Trade Execution
    # ========================================================================
    
    def execute_trade(self, signal_id: str) -> ExecutedTrade:
        """
        Execute an approved trade.
        
        Args:
            signal_id: ID of approved signal
            
        Returns:
            ExecutedTrade record
        """
        approval = self.pending_approvals.get(signal_id)
        if not approval:
            raise ValueError(f"No approval found for: {signal_id}")
        
        if not approval.approved:
            raise ValueError(f"Trade not approved: {signal_id}")
        
        signal = approval.signal
        
        # Use modified values if provided, otherwise use suggested
        position_size = approval.modified_position_size or signal.position_size or 100
        stop_loss = approval.modified_stop_loss or signal.stop_loss
        take_profit = approval.modified_take_profit or signal.take_profit
        
        trade_id = f"TRD_{signal_id}"
        
        trade = ExecutedTrade(
            trade_id=trade_id,
            symbol=signal.symbol,
            signal_id=signal_id,
            entry_price=signal.price,
            entry_date=datetime.now(),
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            status=TradeStatus.EXECUTED
        )
        
        self.executed_trades.append(trade)
        self.pending_signals.remove(signal)
        del self.pending_approvals[signal_id]
        
        self._save_records()
        logger.info(f"✅ Trade executed: {trade_id} ({signal.symbol} {signal.signal_type})")
        
        return trade
    
    def manual_trade(
        self,
        symbol: str,
        signal_type: SignalType,
        entry_price: float,
        position_size: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        notes: str = "Manual entry"
    ) -> 'ExecutedTrade':
        """
        Directly open a trade without going through signal/approval flow.
        For manual record-keeping of trades entered at broker discretion.
        """
        trade_id = f"MAN_{symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        signal_id = f"manual_{trade_id}"

        trade = ExecutedTrade(
            trade_id=trade_id,
            symbol=symbol,
            signal_id=signal_id,
            entry_price=entry_price,
            entry_date=datetime.now(),
            position_size=position_size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            status=TradeStatus.EXECUTED,
            notes=notes
        )

        self.executed_trades.append(trade)
        self._save_records()
        logger.info(f"✅ Manual trade opened: {trade_id} ({symbol} {signal_type.value} @ {entry_price})")
        return trade

    # ========================================================================
    # Trade Closure
    # ========================================================================
    
    def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_reason: str = "Manual close"
    ) -> ExecutedTrade:
        """
        Close an open trade and record P&L.
        
        Args:
            trade_id: ID of trade to close
            exit_price: Exit price
            exit_reason: Why closed (e.g., "Take profit", "Stop loss")
            
        Returns:
            Updated ExecutedTrade record
        """
        trade = next((t for t in self.executed_trades if t.trade_id == trade_id), None)
        if not trade:
            raise ValueError(f"Trade not found: {trade_id}")
        
        if trade.status == TradeStatus.CLOSED:
            raise ValueError(f"Trade already closed: {trade_id}")
        
        # Calculate P&L
        pnl = (exit_price - trade.entry_price) * trade.position_size
        pnl_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100
        
        trade.exit_price = exit_price
        trade.exit_date = datetime.now()
        trade.exit_reason = exit_reason
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent
        trade.status = TradeStatus.CLOSED
        
        self._save_records()
        logger.info(f"✅ Trade closed: {trade_id} (P&L: ${pnl:,.2f}, {pnl_percent:+.2f}%)")
        
        return trade
    
    # ========================================================================
    # Trade History & Analytics
    # ========================================================================
    
    def get_open_trades(self) -> List[Dict]:
        """Get all open trades"""
        open_trades = [t for t in self.executed_trades if t.status == TradeStatus.EXECUTED]
        return [self._trade_to_dict(t) for t in open_trades]
    
    def get_trade_history(self) -> List[Dict]:
        """Get all closed trades"""
        closed_trades = [t for t in self.executed_trades if t.status == TradeStatus.CLOSED]
        return [self._trade_to_dict(t) for t in closed_trades]
    
    def get_performance_stats(self) -> Dict:
        """Calculate performance statistics"""
        closed = [t for t in self.executed_trades if t.status == TradeStatus.CLOSED]
        open_trades = [t for t in self.executed_trades if t.status == TradeStatus.EXECUTED]
        
        total_pnl = sum(t.pnl for t in closed if t.pnl)
        current_cash = self.initial_cash + total_pnl
        
        # Deduct cost of open trades from cash
        for ot in open_trades:
            current_cash -= (ot.entry_price * ot.position_size)
            
        # Total exposure is the current market value of open trades
        # (Using entry price as a proxy if live price not available in this manager)
        total_exposure = sum(ot.entry_price * ot.position_size for ot in open_trades)
        
        if not closed:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
                'best_trade': None,
                'worst_trade': None,
                'total_exposure': total_exposure,
                'current_cash': current_cash
            }
        
        winning = [t for t in closed if t.pnl and t.pnl > 0]
        losing = [t for t in closed if t.pnl and t.pnl < 0]
        
        return {
            'total_trades': len(closed),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'win_rate': (len(winning) / len(closed)) * 100 if closed else 0.0,
            'total_pnl': total_pnl,
            'avg_pnl': total_pnl / len(closed) if closed else 0.0,
            'best_trade': max((t.pnl for t in closed if t.pnl), default=0),
            'worst_trade': min((t.pnl for t in closed if t.pnl), default=0),
            'total_exposure': total_exposure,
            'current_cash': current_cash
        }

    def get_monitored_tickers(self) -> List[str]:
        """Get the configured list of user-monitored tickers."""
        return list(self.monitored_tickers)

    def set_monitored_tickers(self, tickers: List[str], save: bool = True) -> List[str]:
        """Replace monitored tickers with a normalized, de-duplicated list."""
        normalized: List[str] = []
        seen = set()
        for ticker in tickers:
            t = str(ticker).strip().upper()
            if not t or t in seen:
                continue
            seen.add(t)
            normalized.append(t)

        self.monitored_tickers = normalized
        if save:
            self._save_records()
        return self.get_monitored_tickers()
    
    # ========================================================================
    # Persistence
    # ========================================================================
    
    def _save_records(self) -> None:
        """Save records to JSON file"""
        records = {
            'monitored_tickers': self.monitored_tickers,
            'executed_trades': [asdict(t) for t in self.executed_trades],
            'saved_at': datetime.now().isoformat()
        }
        
        with open(self.records_file, 'w') as f:
            json.dump(records, f, indent=2, default=str)
        
        logger.debug(f"Saved {len(self.executed_trades)} trades to {self.records_file}")
    
    def _load_records(self) -> None:
        """Load records from JSON file"""
        if os.path.exists(self.records_file):
            try:
                with open(self.records_file, 'r') as f:
                    records = json.load(f)

                    if 'monitored_tickers' in records and isinstance(records['monitored_tickers'], list):
                        self.set_monitored_tickers(records['monitored_tickers'], save=False)
                    
                    # Load pending signals
                    if 'pending_signals' in records:
                        for sig_dict in records['pending_signals']:
                            signal = TradeSignal(
                                signal_id=sig_dict.get('signal_id'),
                                symbol=sig_dict.get('symbol'),
                                signal_type=SignalType(sig_dict.get('type', 'BUY')),
                                price=sig_dict.get('price', 0),
                                confidence=sig_dict.get('confidence', 0),
                                reason=sig_dict.get('reason', ''),
                                generated_at=datetime.fromisoformat(sig_dict.get('generated_at', datetime.now().isoformat())),
                                position_size=sig_dict.get('position_size'),
                                stop_loss=sig_dict.get('stop_loss'),
                                take_profit=sig_dict.get('take_profit'),
                                atr=sig_dict.get('atr')
                            )
                            self.pending_signals.append(signal)
                    
                    # Load executed trades
                    if 'executed_trades' in records:
                        for trade_dict in records['executed_trades']:
                            trade = ExecutedTrade(
                                trade_id=trade_dict.get('trade_id'),
                                symbol=trade_dict.get('symbol'),
                                signal_id=trade_dict.get('signal_id', ''),
                                entry_price=trade_dict.get('entry_price', 0),
                                entry_date=datetime.fromisoformat(trade_dict.get('entry_date', datetime.now().isoformat())),
                                position_size=trade_dict.get('position_size', 0),
                                stop_loss=trade_dict.get('stop_loss'),
                                take_profit=trade_dict.get('take_profit'),
                                status=TradeStatus(trade_dict.get('status', 'executed')),
                                exit_price=trade_dict.get('exit_price'),
                                exit_date=datetime.fromisoformat(trade_dict['exit_date']) if trade_dict.get('exit_date') else None,
                                exit_reason=trade_dict.get('exit_reason'),
                                pnl=trade_dict.get('pnl'),
                                pnl_percent=trade_dict.get('pnl_percent'),
                                notes=trade_dict.get('notes', '')
                            )
                            self.executed_trades.append(trade)
                    
                    logger.info(f"✅ Loaded {len(self.pending_signals)} signals, {len(self.executed_trades)} trades from {self.records_file}")
            except Exception as e:
                logger.warning(f"Could not load records: {e}")
    
    # ========================================================================
    # Utilities
    # ========================================================================
    
    def _signal_to_dict(self, signal: TradeSignal) -> Dict:
        """Convert signal to dictionary"""
        return {
            'signal_id': signal.signal_id,
            'symbol': signal.symbol,
            'type': signal.signal_type.value,
            'price': signal.price,
            'confidence': signal.confidence,
            'reason': signal.reason,
            'generated_at': signal.generated_at.isoformat(),
            'position_size': signal.position_size,
            'stop_loss': signal.stop_loss,
            'take_profit': signal.take_profit,
            'atr': signal.atr
        }
    
    def _trade_to_dict(self, trade: ExecutedTrade) -> Dict:
        """Convert trade to dictionary"""
        return {
            'trade_id': trade.trade_id,
            'symbol': trade.symbol,
            'entry_price': trade.entry_price,
            'entry_date': trade.entry_date.isoformat(),
            'position_size': trade.position_size,
            'stop_loss': trade.stop_loss,
            'take_profit': trade.take_profit,
            'status': trade.status.value,
            'exit_price': trade.exit_price,
            'exit_date': trade.exit_date.isoformat() if trade.exit_date else None,
            'exit_reason': trade.exit_reason,
            'pnl': trade.pnl,
            'pnl_percent': trade.pnl_percent,
            'notes': trade.notes
        }
