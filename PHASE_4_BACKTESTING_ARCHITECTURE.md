# Phase 4 Backtesting Engine - Architecture & Design

**System Design and Architecture Documentation**

---

## 🏗️ System Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────┐
│         Phase 4: Backtesting Engine             │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────────────────────────────┐   │
│  │  BacktestEngine (Main Controller)        │   │
│  │  - Portfolio tracking                    │   │
│  │  - Trade lifecycle management            │   │
│  │  - Position sizing                       │   │
│  │  - Metrics calculation                   │   │
│  └──────────────────────────────────────────┘   │
│           ↓                ↓           ↓         │
│  ┌──────────────┐  ┌──────────────┐ ┌─────────┐ │
│  │Trade Objects │  │Portfolio     │ │Snapshots│ │
│  │- Entry/Exit  │  │Tracking      │ │- State  │ │
│  │- P&L         │  │- Cash        │ │  Record │ │
│  │- Duration    │  │- Positions   │ │        │ │
│  └──────────────┘  └──────────────┘ └─────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
         ↓                    ↑
   Phase 1, 2, 3         Results & Metrics
```

---

## 📦 Class Architecture

### BacktestEngine Class

**Responsibility**: Main orchestrator for portfolio simulation

**Key Components**:
```
BacktestEngine
├── Portfolio State
│   ├── initial_capital: float
│   ├── cash: float
│   ├── open_trades: Dict[str, Trade]
│   └── closed_trades: List[Trade]
│
├── Configuration
│   ├── max_portfolio_exposure: float
│   ├── max_position_size: float
│   ├── max_open_positions: int
│   ├── risk_per_trade: float
│   └── commission_percent: float
│
├── History
│   └── portfolio_history: List[PortfolioSnapshot]
│
└── Methods
    ├── calculate_position_size()
    ├── open_trade()
    ├── close_trade()
    ├── can_open_position()
    ├── mark_to_market()
    ├── record_snapshot()
    ├── get_performance_metrics()
    ├── get_portfolio_value()
    ├── get_open_positions_value()
    ├── calculate_portfolio_exposure()
    └── adjust_position_size_for_exposure()
```

### Trade Dataclass

**Responsibility**: Track individual trades

**Structure**:
```
Trade
├── Entry Information
│   ├── ticker: str
│   ├── entry_date: datetime
│   ├── entry_price: float
│   ├── entry_signal: str ("BUY"/"SELL")
│   └── entry_confidence: float
│
├── Position Information
│   ├── position_size: int (shares)
│   ├── position_value: float ($)
│   └── atr: float
│
├── Exit Information (Optional)
│   ├── exit_date: Optional[datetime]
│   ├── exit_price: Optional[float]
│   └── exit_reason: Optional[str]
│
├── P&L Information (Optional)
│   ├── pnl: Optional[float] ($)
│   ├── pnl_percent: Optional[float] (%)
│   └── duration_days: Optional[int]
│
└── Methods
    └── close_trade()
```

### PortfolioSnapshot Dataclass

**Responsibility**: Capture portfolio state at a point in time

**Structure**:
```
PortfolioSnapshot
├── date: datetime
├── cash: float
├── open_positions_value: float
├── closed_trades_value: float
├── total_value: float
├── open_position_count: int
└── closed_trade_count: int
```

---

## 🔄 State Transitions

### Trade State Machine

```
                  ┌─────────────────┐
                  │   NEW SIGNAL    │
                  └────────┬────────┘
                           ↓
                  ┌─────────────────┐
        ┌────────→│ VALIDATE LIMITS │←──────┐
        │         └────────┬────────┘       │
        │                  ↓                 │
        │         ┌─────────────────┐       │
        │         │CREATE TRADE OBJ │       │
        │         └────────┬────────┘       │
        │                  ↓                 │
        │         ┌─────────────────┐       │
        │         │OPEN TRADE EVENT │       │
        │         │- Add to Dict    │       │
        │         │- Deduct Cash    │       │
        │         └────────┬────────┘       │
        │                  ↓                 │
        │         ┌─────────────────┐       │
        │         │   MARK-TO-MTM   │───────┤
        │         │ (Daily Updates) │       │
        │         └────────┬────────┘       │
        │                  ↓                 │
        │         ┌─────────────────┐       │
        │         │   EXIT SIGNAL   │       │
        │         │   (Take Profit) │       │
        │         │   (Stop Loss)   │       │
        │         └────────┬────────┘       │
        │                  ↓                 │
        │         ┌─────────────────┐       │
        │         │CLOSE TRADE EVENT│       │
        │         │- Calc P&L       │       │
        │         │- Add to History │       │
        │         │- Return Cash    │       │
        │         └────────┬────────┘       │
        │                  ↓                 │
        │         ┌─────────────────┐       │
        │         │    SNAPSHOT     │       │
        │         │ (Daily Record)  │       │
        │         └─────────────────┘       │
        │                                    │
        └────────────────────────────────────┘
              (Continue Trading)
```

### Portfolio State Machine

```
    ┌──────────────┐
    │ INITIALIZED  │ (100,000 cash, 0 positions)
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │   TRADING    │ (Positions open/close)
    │   CYCLE      │
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │PORTFOLIO DAY │ (Snapshot recorded)
    │RECORD        │
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │   METRICS    │ (Calculate performance)
    │   READY      │
    └──────────────┘
```

---

## 📊 Data Flow Diagrams

### Trade Opening Flow

```
Signal Generated (AAPL, $150, 75% conf, ATR=$3)
    ↓
calculate_position_size()
├─ account_equity = $100,000
├─ risk = 2%
├─ base_size = (100k × 0.02) / (150 × 3) = 44 shares
└─ adjusted = 44 × (75/100) = 33 shares
    ↓
can_open_position()
├─ Check: open_count (1) < max (5) ✓
├─ Check: exposure (10%) < max (50%) ✓
├─ Check: cash ($100k) > required ✓
└─ Result: APPROVED
    ↓
open_trade()
├─ Create Trade object
├─ position_value = 33 × $150 = $4,950
├─ commission = $4,950 × 0.1% = $4.95
├─ Add to open_trades["AAPL"]
├─ cash -= $4,950 + $4.95 = $95,045.05
└─ Return Trade object
    ↓
✅ Trade Opened: 33 AAPL @ $150
```

### Mark-to-Market Flow

```
New Day: prices = {"AAPL": $160, ...}
    ↓
mark_to_market()
├─ For each open_trade:
│  ├─ AAPL: position_value = 33 × $160 = $5,280
│  └─ Previous: $4,950
├─ Unrealized P&L = $5,280 - $4,950 = +$330
└─ Portfolio updated
    ↓
Portfolio Value Updated:
├─ Cash: $95,045.05
├─ Open Positions: $5,280
├─ Total: $100,325.05 (gain: +$325.05)
    ↓
✅ Marked-to-Market Complete
```

### Performance Metrics Flow

```
Closed Trades: [Trade1, Trade2, ...]
    ↓
Aggregate Calculations:
├─ Winners:
│  ├─ Trade1: +$600 ✓
│  ├─ Trade3: +$400 ✓
│  └─ Count: 2
├─ Losers:
│  ├─ Trade2: -$200 ✗
│  └─ Count: 1
├─ Totals:
│  ├─ Gross Wins: $1,000
│  ├─ Gross Losses: -$200
│  └─ Net: +$800
    ↓
Calculate Ratios:
├─ Win Rate: 2/3 = 66.7%
├─ Profit Factor: 1000/200 = 5.0
├─ Avg Winner: 1000/2 = $500
├─ Avg Loser: -200/1 = -$200
└─ Avg R/R: 500/200 = 2.5
    ↓
✅ Metrics Ready for Analysis
```

---

## 🔀 Integration Points

### Phase 1 Integration
**Input**: Historical OHLC data from market data collector
```
Market_Data
├─ Date: 2024-01-01
├─ Open: $149.50
├─ High: $152.00
├─ Low: $149.00
├─ Close: $150.25
└─ Volume: 1M

Used for:
├─ Price lookups in mark_to_market()
├─ ATR calculation (for position sizing)
└─ Historical backtesting
```

### Phase 2 Integration
**Input**: Signals and technical indicators from signal engine
```
Signal
├─ Ticker: "AAPL"
├─ Action: "BUY"
├─ Confidence: 75
├─ Price: $150.25
├─ ATR: $3.00
└─ Reason: "Golden Cross"

Used for:
├─ Trade opening trigger
├─ Position sizing (ATR, confidence)
└─ Exit signal generation
```

### Phase 3 Integration
**Input**: Risk management parameters and calculations
```
RiskEngine provides:
├─ max_portfolio_exposure: 0.50 (50%)
├─ max_position_size: 0.10 (10%)
├─ Position sizing formula
└─ Risk calculations

Used for:
├─ Portfolio exposure check
├─ Position size adjustment
├─ Constraint validation
└─ Capital allocation
```

---

## 🔧 Algorithm Details

### Kelly Criterion Calculation

**Formula**:
```
f* = (edge × avg_win - (1 - edge) × avg_loss) / avg_win

Simplified for ATR-based sizing:
f* = (account_equity × risk_percent) / (entry_price × atr) × confidence_factor
```

**Implementation**:
```python
def calculate_position_size(entry_price, atr, confidence):
    account_equity = self.cash + self.get_open_positions_value()
    risk_amount = account_equity * self.risk_per_trade
    
    base_size = int(risk_amount / (entry_price * atr))
    
    adjusted_size = base_size * (confidence / 100)
    
    max_size_by_percent = int((account_equity * self.max_position_size) / entry_price)
    
    return min(adjusted_size, max_size_by_percent)
```

### Portfolio Exposure Calculation

**Logic**:
```python
def calculate_portfolio_exposure():
    portfolio_value = get_portfolio_value()
    open_positions = get_open_positions_value()
    exposure = (open_positions / portfolio_value) × 100
    
    return {
        "current_exposure": exposure,
        "remaining_capacity": 100 - exposure,
        "at_limit": exposure >= max_portfolio_exposure
    }
```

### P&L Calculation

**For BUY trades**:
```
P&L = (exit_price - entry_price) × position_size - commission_both_ways
P&L_percent = (P&L / entry_value) × 100
```

**For SELL trades** (short):
```
P&L = (entry_price - exit_price) × position_size - commission_both_ways
P&L_percent = (P&L / entry_value) × 100
```

---

## 📈 Performance Considerations

### Time Complexity
| Operation | Complexity | Notes |
|-----------|-----------|-------|
| open_trade() | O(1) | Direct dict operations |
| close_trade() | O(1) | Direct lookup and removal |
| mark_to_market() | O(n) | n = open positions |
| get_performance_metrics() | O(m) | m = closed trades |
| record_snapshot() | O(1) | Append to list |

### Space Complexity
| Component | Space | Notes |
|-----------|-------|-------|
| open_trades | O(n) | n = max 5 positions |
| closed_trades | O(m) | m = total trades |
| portfolio_history | O(d) | d = trading days |

### Optimization Tips
- Batch operations on same day
- Pre-allocate snapshot array
- Limit history size if needed
- Cache aggregation results

---

## 🔐 Data Integrity

### Validation Rules
```
On Trade Open:
├─ Ticker: non-empty string ✓
├─ Entry Price: > 0 ✓
├─ Date: valid datetime ✓
├─ Signal: "BUY" or "SELL" ✓
├─ Confidence: 0-100 ✓
└─ ATR: > 0 ✓

On Trade Close:
├─ Ticker: exists in open_trades ✓
├─ Exit Price: > 0 ✓
├─ Date: >= entry_date ✓
└─ Reason: non-empty string ✓

Portfolio State:
├─ cash >= 0 ✓
├─ position_size >= 0 ✓
├─ position_value >= 0 ✓
└─ total_value >= 0 ✓
```

### Invariants
```
Always True:
├─ portfolio_value = cash + open_positions + closed_pnl
├─ open_trade_count <= max_open_positions
├─ portfolio_exposure <= max_portfolio_exposure (enforced)
└─ position_size <= max_position_size (enforced)
```

---

## 🧪 Testing Architecture

### Test Pyramid
```
        ▲
       ╱ ╲
      ╱   ╲  Integration Tests (1-2)
     ╱     ╲ - Full workflow
    ╱───────╲
   ╱         ╲ Unit Tests (8-9)
  ╱           ╲ - Individual methods
 ╱─────────────╲
╱               ╲ Test Fixtures
╱_______________╲ - Setup/teardown
```

### Test Categories
```
Functionality Tests (4):
├─ test_engine_initialization
├─ test_open_trade
├─ test_close_trade
└─ test_performance_metrics

Constraint Tests (2):
├─ test_portfolio_exposure_limit
└─ test_multiple_positions

Algorithm Tests (2):
├─ test_position_sizing
└─ test_mark_to_market

State Tests (2):
├─ test_portfolio_snapshot
└─ test_drawdown_tracking
```

---

## 📚 Related Docs

- [PHASE_4_BACKTESTING_INDEX.md](PHASE_4_BACKTESTING_INDEX.md)
- [PHASE_4_BACKTESTING_CODE_REFERENCE.md](PHASE_4_BACKTESTING_CODE_REFERENCE.md)
- [PHASE_4_BACKTESTING_TEST_GUIDE.md](PHASE_4_BACKTESTING_TEST_GUIDE.md)
