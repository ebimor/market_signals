# Phase 4c: Visual Architecture & Workflow Guide

## 🏗️ Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       FastAPI Application                       │
│                   (backend/main.py)                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Trading Router Integration                    │
│              (backend/api/trading.py - 300+ lines)               │
├─────────────────────────────────────────────────────────────────┤
│ POST /api/trading/signals     - Create signal                   │
│ GET  /api/trading/signals     - Get pending                     │
│ POST /api/trading/approve     - Approve signal                  │
│ POST /api/trading/reject      - Reject signal                   │
│ POST /api/trading/execute     - Execute trade                   │
│ POST /api/trading/close       - Close trade                     │
│ GET  /api/trading/trades/open - Get open positions             │
│ GET  /api/trading/trades/history - Get closed trades           │
│ GET  /api/trading/stats       - Get performance stats           │
│ GET  /api/trading/dashboard   - Get complete dashboard          │
│ GET  /api/trading/status      - Get system status               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              TradeManager Core Logic                             │
│        (backend/trading/trade_manager.py - 450+ lines)           │
├─────────────────────────────────────────────────────────────────┤
│ Classes:                                                        │
│  ├─ TradeSignal (signal suggestions)                           │
│  ├─ ExecutedTrade (trade records)                              │
│  ├─ TradeApproval (approval records)                           │
│  ├─ TradeStatus enum (state machine)                           │
│  └─ SignalType enum (BUY/SELL/EXIT)                            │
│                                                                 │
│ Methods:                                                        │
│  ├─ add_signal() → Create suggestion                           │
│  ├─ approve_trade() → User approves                            │
│  ├─ reject_trade() → User rejects                              │
│  ├─ execute_trade() → Open position                            │
│  ├─ close_trade() → Close with P&L                             │
│  ├─ get_pending_signals() → List pending                       │
│  ├─ get_open_trades() → List open                              │
│  ├─ get_trade_history() → List closed                          │
│  └─ get_performance_stats() → Analytics                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────┬──────────────────────┬──────────────────┐
│   Signal Generation  │  Risk Management     │  Data Persistence│
│   (Phase 2)          │  (Phase 3)           │  (JSON Storage)  │
│                      │                      │                  │
│ ├─ RSI Indicator     │ ├─ Portfolio Limits  │ ├─ Signals       │
│ ├─ MACD Indicator    │ │  (50% max exposure)│ ├─ Trades        │
│ ├─ SMA Confluence    │ ├─ Position Sizing   │ └─ Approvals     │
│ └─ Confidence Score  │ │  (10% max)         │                  │
│                      │ └─ Validation        │                  │
└──────────────────────┴──────────────────────┴──────────────────┘
                              ↓
┌──────────────────────┬──────────────────────┬──────────────────┐
│  Data Management     │  Backtesting Engine  │  Database        │
│  (Phase 1)           │  (Phase 4)           │                  │
│                      │                      │                  │
│ ├─ yfinance Downloads│ ├─ Trade Execution   │ ├─ SQLite        │
│ ├─ CSV Caching       │ ├─ P&L Calculation   │ └─ Initialization│
│ └─ Multi-Symbol      │ └─ Performance Stats │                  │
└──────────────────────┴──────────────────────┴──────────────────┘
```

---

## 🔄 Manual Approval Workflow (Step by Step)

```
PHASE 1: Signal Generation (No User Input)
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Market Data → Indicators → Analysis → Signal           │
│  (OHLCV)     (RSI, MACD) (Confluence) (Suggestion)      │
│                                                          │
│  Input: Historical prices                               │
│  Output: BUY/SELL signal with entry/exit levels        │
│  Time: <100ms                                            │
│  User Interaction: ❌ NONE                               │
│                                                          │
└──────────────────────────────────────────────────────────┘
                            ↓
PHASE 2: Signal Pending (Awaits User Review)
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Signal Created in PENDING state                        │
│  ✓ Ready for user review                                │
│  ✓ Stored in JSON file                                  │
│  ✓ API accessible via GET /signals                      │
│                                                          │
│  Signal Details:                                        │
│  ├─ signal_id: Unique identifier                        │
│  ├─ symbol: Stock ticker (AAPL, TSLA, etc.)           │
│  ├─ type: BUY or SELL                                   │
│  ├─ price: Suggested entry price                        │
│  ├─ confidence: 0-100 confidence score                  │
│  ├─ reason: Why signal generated                        │
│  ├─ position_size: Suggested # of shares                │
│  ├─ stop_loss: Suggested stop level                     │
│  └─ take_profit: Suggested profit target                │
│                                                          │
│  User Interaction: ⏳ REVIEW REQUIRED                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
                            ↓
PHASE 3: User Reviews & Makes Decision (MANUAL)
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  USER ACTIONS:                                          │
│                                                          │
│  Option A: APPROVE                                      │
│  ├─ Review signal details                               │
│  ├─ Check chart analysis                                │
│  ├─ Can modify: position_size, SL, TP                   │
│  └─ Send: POST /approve with modifications              │
│                                                          │
│  Option B: REJECT                                       │
│  ├─ Find signal too risky                               │
│  ├─ Don't like entry level                              │
│  └─ Send: POST /reject                                  │
│                                                          │
│  Option C: IGNORE                                       │
│  ├─ Don't act on signal                                 │
│  └─ Signal expires or user dismisses                    │
│                                                          │
│  User Interaction: ✅ DECISION REQUIRED                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
                            ↓
        ┌─────────────────┴─────────────────┐
        ↓                                   ↓
   APPROVED                             REJECTED
        │                                   │
        │                          Signal Status: REJECTED
        │                          (Deleted/Archived)
        │                          (No Trade Executed)
        │
        ↓
PHASE 4: Approved Signal (Ready for Execution)
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Signal Status: APPROVED                                │
│                                                          │
│  If User Modified:                                      │
│  ├─ position_size: 100 → 75 shares                      │
│  ├─ stop_loss: $148 → $148.50 (tighter)                 │
│  └─ take_profit: $155 → $156 (higher target)            │
│                                                          │
│  Stored with Approval Record:                           │
│  ├─ approval_id: Unique identifier                      │
│  ├─ signal_id: Link to signal                           │
│  ├─ approval_notes: User comment                        │
│  ├─ modifications: What user changed                    │
│  └─ approved_at: Timestamp                              │
│                                                          │
│  User Interaction: ✅ COMPLETE                          │
│                                                          │
└──────────────────────────────────────────────────────────┘
                            ↓
PHASE 5: Trade Execution (Automatic)
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  System reads APPROVED signal                           │
│  Validates all conditions                               │
│  Executes trade with user-approved parameters:          │
│  ├─ Entry Price: $150.25                                │
│  ├─ Position Size: 75 shares (modified)                 │
│  ├─ Stop Loss: $148.50 (modified)                       │
│  └─ Take Profit: $156.00 (modified)                     │
│                                                          │
│  Trade Created:                                         │
│  ├─ trade_id: TRD_AAPL_20260517_...                    │
│  ├─ status: EXECUTED                                    │
│  ├─ entry_date: 2026-05-17T15:06:35                    │
│  └─ (stored in executed_trades)                         │
│                                                          │
│  User Interaction: ❌ NONE (Automatic)                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
                            ↓
PHASE 6: Position Monitoring (Automatic)
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Real-Time Monitoring:                                  │
│  ├─ Entry Price: $150.25                                │
│  ├─ Current Price: $153.50 (example)                    │
│  ├─ Position Value: $153.50 × 75 = $11,512.50           │
│  ├─ Cost Basis: $150.25 × 75 = $11,268.75              │
│  ├─ Unrealized P&L: +$243.75                            │
│  └─ Unrealized Return: +2.16%                           │
│                                                          │
│  Distance to Targets:                                   │
│  ├─ Distance to TP: $156.00 - $153.50 = $2.50           │
│  ├─ Distance to SL: $153.50 - $148.50 = $5.00           │
│  └─ Risk/Reward: Favorable                              │
│                                                          │
│  User Interaction: ⏳ MONITOR (can check via API)       │
│                                                          │
└──────────────────────────────────────────────────────────┘
                            ↓
PHASE 7: Exit Signal Generated (Automatic)
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  When EITHER condition is met:                          │
│  ├─ Price reaches TP: $156.00                           │
│  └─ Price hits SL: $148.50                              │
│                                                          │
│  System alerts user with exit signal                    │
│  (Exact mechanism depends on integration)               │
│                                                          │
│  Example: Price reaches $156.00                         │
│  → System suggests: "SELL at take profit $156.00"       │
│  → Signal generated (SELL type)                         │
│  → User must confirm execution                          │
│                                                          │
│  User Interaction: ⏳ CONFIRMATION NEEDED                │
│                                                          │
└──────────────────────────────────────────────────────────┘
                            ↓
PHASE 8: User Confirms Exit (MANUAL)
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  USER ACTION:                                           │
│  ├─ Receive exit signal/alert                           │
│  ├─ Verify it's correct                                 │
│  └─ Call: POST /close with exit_price and reason        │
│                                                          │
│  Input to /close:                                       │
│  ├─ trade_id: TRD_AAPL_20260517_...                    │
│  ├─ exit_price: 156.00                                  │
│  └─ exit_reason: "Take profit reached"                  │
│                                                          │
│  User Interaction: ✅ DECISION REQUIRED                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
                            ↓
PHASE 9: Trade Closure & P&L Calculation (Automatic)
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  System closes trade:                                   │
│  ├─ entry_price: $150.25                                │
│  ├─ position_size: 75 shares                            │
│  ├─ exit_price: $156.00                                 │
│  └─ exit_date: 2026-05-17T15:30:00                     │
│                                                          │
│  P&L Calculation:                                       │
│  ├─ Gross P&L: ($156.00 - $150.25) × 75 = $432.50      │
│  ├─ Return %: $432.50 / ($150.25 × 75) = 3.83%         │
│  └─ Status: CLOSED                                      │
│                                                          │
│  Trade Final Record:                                    │
│  {                                                      │
│    "trade_id": "TRD_AAPL_20260517_...",                │
│    "status": "closed",                                  │
│    "entry_price": 150.25,                               │
│    "exit_price": 156.00,                                │
│    "position_size": 75,                                 │
│    "pnl": 432.50,                                       │
│    "pnl_percent": 3.83,                                 │
│    "duration": "24 minutes"                             │
│  }                                                      │
│                                                          │
│  User Interaction: ❌ NONE (Automatic)                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
                            ↓
PHASE 10: Analytics & Performance (Automatic)
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Trade Added to History                                 │
│  Performance Stats Updated:                             │
│  ├─ Total Trades: 5                                     │
│  ├─ Winning Trades: 4                                   │
│  ├─ Losing Trades: 1                                    │
│  ├─ Win Rate: 80%                                       │
│  ├─ Total P&L: $1,234.50                                │
│  ├─ Average P&L: $246.90                                │
│  ├─ Best Trade: $567.00                                 │
│  ├─ Worst Trade: -$145.00                               │
│  └─ Max Drawdown: -2.3%                                 │
│                                                          │
│  Available via: GET /stats                              │
│                                                          │
│  User Interaction: ⏳ REVIEW (via API)                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 📊 API Endpoint Quick Reference

```
SIGNAL GENERATION
  Signal Created  → POST /api/trading/signals
  ├─ Returns: signal_id, all signal details
  └─ Status: PENDING

SIGNAL REVIEW
  Get Pending     → GET /api/trading/signals
  └─ Returns: List of all pending signals

SIGNAL APPROVAL
  Approve         → POST /api/trading/approve
  ├─ Can modify: position_size, stop_loss, take_profit
  └─ Status: APPROVED
  
  OR Reject       → POST /api/trading/reject
  └─ Status: REJECTED (deleted)

TRADE EXECUTION
  Execute         → POST /api/trading/execute
  ├─ Only works if APPROVED
  └─ Returns: trade_id, entry details

POSITION MONITORING
  Get Open        → GET /api/trading/trades/open
  └─ Returns: All active positions with unrealized P&L

TRADE CLOSURE
  Close           → POST /api/trading/close
  ├─ Takes: trade_id, exit_price, exit_reason
  └─ Returns: trade details with P&L

REPORTING
  History         → GET /api/trading/trades/history
  ├─ Returns: All closed trades
  └─ With: entry, exit, P&L, duration
  
  Stats           → GET /api/trading/stats
  ├─ Returns: Win rate, total P&L, best/worst
  └─ Analytics: All performance metrics
  
  Dashboard       → GET /api/trading/dashboard
  ├─ Returns: Everything at once
  └─ Signals + Trades + Stats + History
```

---

## 🎯 User Interaction Points (MANUAL)

```
User Must Decide:

1. SIGNAL REVIEW ✅
   Action: Review pending signals
   API: GET /api/trading/signals
   Decision: Approve? Reject? Ignore?
   
2. SIGNAL APPROVAL ✅
   Action: Approve signal for execution
   API: POST /api/trading/approve
   Decision: Accept as-is? Modify? Reject?
   
3. EXIT CONFIRMATION ✅
   Action: Confirm trade closure at TP/SL
   API: POST /api/trading/close
   Decision: Close now? Wait? Adjust exit price?

Everything Else: AUTOMATIC (No user interaction)
├─ Signal generation ❌ No user input
├─ Trade execution ❌ No user input
├─ Position monitoring ❌ No user input
├─ P&L calculation ❌ No user input
└─ Record storage ❌ No user input
```

---

## 💾 Data Flow

```
yfinance
   ↓
Historical Data
   ↓
Signal Generation (Phase 2)
   ├─ RSI Indicator
   ├─ MACD Indicator
   └─ SMA Confluence
   ↓
Trade Signal Created
   ├─ Stored in JSON
   └─ Status: PENDING
   ↓
User Reviews & Decides
   ├─ Approves → Status: APPROVED
   ├─ Rejects → Status: REJECTED
   └─ Modifies → Stores modifications
   ↓
System Executes (If Approved)
   ├─ Creates ExecutedTrade
   ├─ Stores with entry details
   └─ Status: EXECUTED
   ↓
System Monitors Position
   ├─ Tracks unrealized P&L
   └─ Monitors TP/SL levels
   ↓
Exit Signal Generated
   ├─ At TP: Take profit level
   └─ At SL: Stop loss level
   ↓
User Confirms Exit
   ├─ Calls POST /close
   └─ Provides exit_price
   ↓
System Closes Trade
   ├─ Calculates P&L
   ├─ Updates status: CLOSED
   └─ Stores in history
   ↓
Performance Analytics
   ├─ Updates win rate
   ├─ Calculates total P&L
   └─ Computes best/worst trades
```

---

## 🔐 Safety & Control

```
AUTOMATIC (System Controlled)          MANUAL (User Controlled)
─────────────────────────────────    ──────────────────────────────
✓ Signal Generation                   ✓ Signal Approval
✓ Trade Execution (if approved)       ✓ Exit Confirmation
✓ Position Monitoring                 ✓ Position Modifications
✓ P&L Calculation                     ✓ Risk/Reward Assessment
✓ Exit Signal Generation              ✓ Trade Timing
✓ Record Storage                       ✓ Entry/Exit Prices
                                       ✓ Position Sizes

GUARANTEE: No trade executes without user confirmation ✅
GUARANTEE: User can modify before execution ✅
GUARANTEE: All decisions are logged ✅
```

---

## 📈 Example Trade Visualization

```
                PRICE MOVEMENT
                    │
         TP ($156) ┤─ ─ ─ ─ ─ ─ ─ ─
                   │  Exit at TP
                   │  P&L: +$432.50
                   │  Return: +3.83%
     Entry ($150) ┤═════●
                   │  Current: $153.50
                   │  Unrealized: +$243.75
                   │
           SL ($148.50) ┤─ ─ ─ ─ ─ ─
                   │
                   └─────────────────────→ TIME

TIMELINE:
15:06:35 - Signal generated
15:07:00 - User reviews & approves
15:07:30 - Trade executes at $150.25
15:20:00 - Price at $153.50 (unrealized +2.16%)
15:30:00 - Price reaches $156.00
15:30:30 - User confirms exit at TP
15:30:45 - Trade closed, P&L recorded (+$432.50)
```

---

## ✅ Implementation Status

- ✅ Signal generation (Phase 2)
- ✅ Risk management (Phase 3)
- ✅ Backtesting engine (Phase 4)
- ✅ Strategy simulator (Phase 4b)
- ✅ Trading REST API (Phase 4c) ← **YOU ARE HERE**
- ⏳ Dashboard & visualization (Phase 4d)
- ⏳ Live trading integration (Phase 5)

All components working and tested. Ready for next phase.
