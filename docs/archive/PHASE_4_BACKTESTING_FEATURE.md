# Phase 4: Backtesting Engine - Feature Documentation

**Complete Feature Reference**

---

## Feature Overview

The Phase 4 Backtesting Engine provides a complete simulation framework for trading strategies on historical data.

---

## 🎯 Core Features

### 1. Trade Management

#### Feature: Open Trade
**Purpose**: Create a new trade with validation
**Input**: Ticker, date, entry price, signal, confidence, ATR
**Output**: Trade object or None if validation fails
**Validation**:
- Check open position count < max (5)
- Check portfolio exposure < max (50%)
- Check sufficient cash available
- Apply position size limits

```python
trade = engine.open_trade(
    ticker="AAPL",
    date=datetime(2024, 1, 1),
    entry_price=150,
    signal="BUY",
    confidence=75,
    atr=3
)
```

#### Feature: Close Trade
**Purpose**: Exit trade and calculate P&L
**Input**: Ticker, date, exit price, reason
**Output**: Closed Trade object with P&L
**Calculation**:
- P&L = (exit_price - entry_price) × position_size
- Minus commission on exit
- Return % = P&L / entry_value

```python
closed = engine.close_trade(
    ticker="AAPL",
    date=datetime(2024, 1, 10),
    exit_price=162,
    reason="Take Profit"
)
```

### 2. Position Sizing

#### Feature: Kelly Criterion Sizing
**Purpose**: Calculate optimal position size
**Formula**:
```
base_size = (account_equity × risk_percent) / (entry_price × atr)
adjusted_size = base_size × (confidence / 100)
```

**Parameters**:
- Account equity: $100,000 (example)
- Risk per trade: 2%
- Entry price: $150
- ATR: $3
- Confidence: 75%

**Example**:
```
base_size = (100000 × 0.02) / (150 × 3) = 44 shares
adjusted = 44 × (75/100) = 33 shares
```

**Constraints Applied**:
- Max 10% per position
- Respects max open positions (5)
- Respects portfolio exposure (50%)
- Reduced proportionally if limits exceeded

#### Feature: Automatic Position Adjustment
**Purpose**: Reduce position size if portfolio exposure exceeded
**Trigger**: When new position would exceed max exposure
**Action**: Proportionally reduce position size
**Result**: Ensures compliance with limits

### 3. Portfolio Management

#### Feature: Portfolio Tracking
**Purpose**: Track total portfolio value over time
**Components**:
- Cash balance
- Open positions value (mark-to-market)
- Closed trades realized P&L
- Total portfolio value

**Calculation**:
```
Portfolio Value = Cash + Open Positions Value + Closed P&L
```

**Example**:
```
Cash: $85,000
Open Positions: $12,000
Closed P&L: $3,500
Total: $100,500
```

#### Feature: Mark-to-Market Updates
**Purpose**: Update unrealized P&L daily
**Input**: Date and ticker → price mapping
**Update**: Position value based on current price
**Impact**: Affects portfolio value and metrics

```python
engine.mark_to_market(
    datetime(2024, 1, 5),
    {"AAPL": 160, "TSLA": 250}
)
```

#### Feature: Portfolio Snapshots
**Purpose**: Record portfolio state at each time period
**Captured**:
- Date
- Cash available
- Open positions value
- Closed trades P&L
- Total portfolio value
- Position counts

**Use**: Build equity curve and analyze drawdown

```python
engine.record_snapshot(datetime(2024, 1, 5))
```

### 4. Performance Metrics

#### Feature: Trade Statistics
**Metrics**:
- Total trades
- Winning trades
- Losing trades
- Win rate (%)

**Example**:
- Total: 42 trades
- Winners: 28
- Losers: 14
- Win Rate: 66.7%

#### Feature: Profitability Metrics
**Metrics**:
- Gross wins ($)
- Gross losses ($)
- Profit factor (wins / losses)
- Net P&L ($)
- Total return (%)

**Example**:
- Gross wins: $18,500
- Gross losses: -$8,000
- Profit factor: 2.31
- Net P&L: $10,500
- Return: 10.50%

#### Feature: Trade Details
**Metrics**:
- Average winner ($)
- Average loser ($)
- Largest win ($)
- Largest loss ($)
- Average duration (days)

**Example**:
- Avg winner: $660.71
- Avg loser: -$571.43
- Largest win: $2,100
- Largest loss: -$1,200
- Avg days: 8.5

#### Feature: Risk Metrics
**Metrics**:
- Win rate (%)
- Loss rate (%)
- Risk/reward ratio
- Maximum drawdown (%)
- Return/drawdown ratio

### 5. Risk Management Integration (Phase 3)

#### Feature: Portfolio Exposure Limits
**Purpose**: Enforce maximum deployed capital
**Limit**: 50% of portfolio
**Implementation**: Calculated before opening trade
**Action**: Reject if exceeds limit
**Alternative**: Reduce position size to fit

```python
exposure = engine.calculate_portfolio_exposure()
# Returns: current %, available %, at_limit bool
```

#### Feature: Position Size Limits
**Purpose**: Prevent over-concentration
**Limits**:
- Max 10% per individual position
- Max 5 concurrent positions
- Max 50% total portfolio exposure

**Enforcement**: Applied before trade opens
**Result**: Balanced portfolio allocation

#### Feature: Risk Per Trade
**Purpose**: Standard risk allocation
**Rate**: 2% per trade
**Application**: In Kelly Criterion calculation
**Adjustment**: Modified by confidence score

### 6. Data Management

#### Feature: Open Trades Dictionary
**Purpose**: Track active positions
**Structure**: {ticker → Trade object}
**Updates**: 
- Added on trade open
- Removed on trade close
- Mark-to-market updates price

```python
engine.open_trades  # {"AAPL": Trade, "TSLA": Trade}
```

#### Feature: Closed Trades List
**Purpose**: Historical trade log
**Structure**: [Trade, Trade, ...]
**Content**:
- Entry/exit prices
- P&L
- Duration
- Reason closed

```python
engine.closed_trades  # [Trade1, Trade2, ...]
```

#### Feature: Portfolio History
**Purpose**: Track equity over time
**Structure**: [PortfolioSnapshot, ...]
**Content**:
- Date-indexed portfolio states
- Portfolio value at each point
- Position counts
- Cash available

```python
engine.portfolio_history  # [Snapshot1, Snapshot2, ...]
```

### 7. Edge Case Handling

#### Feature: Insufficient Capital Check
**Trigger**: Not enough cash for position
**Action**: Return None (trade rejected)
**Message**: "Insufficient capital"

#### Feature: Position Limit Check
**Trigger**: Already at max 5 positions
**Action**: Return None (trade rejected)
**Message**: "Max positions exceeded"

#### Feature: Exposure Limit Check
**Trigger**: Trade would exceed 50% exposure
**Action**: Reduce position size or reject
**Option**: Can scale down to fit

#### Feature: Invalid Trade Close
**Trigger**: Ticker not in open_trades
**Action**: Return None (close failed)
**Message**: "Trade not found"

### 8. Validation & Error Handling

#### Feature: Input Validation
- Price > 0
- Date is valid datetime
- Ticker is string
- Confidence 0-100
- ATR > 0

#### Feature: State Validation
- Cash >= 0
- Position sizes >= 0
- P&L calculations correct
- Portfolio value >= 0

#### Feature: Constraint Validation
- Position count < max
- Exposure < 50%
- Position size < 10%

---

## 📊 Data Flow

### Trade Opening Flow
```
Signal Generated
    ↓
Calculate Position Size (Kelly)
    ↓
Check Portfolio Exposure
    ↓
Validate Capital Available
    ↓
Validate Position Limits
    ↓
Create Trade Object
    ↓
Add to Open Trades
    ↓
Update Cash Balance
    ↓
Return Trade
```

### Trade Closing Flow
```
Close Signal
    ↓
Find Trade by Ticker
    ↓
Calculate P&L
    ↓
Apply Commission
    ↓
Update Cash Balance
    ↓
Move to Closed Trades
    ↓
Remove from Open Trades
    ↓
Return Closed Trade
```

### Daily Update Flow
```
Market Open
    ↓
Receive New Prices
    ↓
Mark-to-Market All Positions
    ↓
Update Unrealized P&L
    ↓
Check Stop Losses
    ↓
Generate Entry/Exit Signals
    ↓
Execute Trades
    ↓
Record Portfolio Snapshot
    ↓
Market Close
```

---

## 🔧 Configuration

### Engine Parameters
```python
BacktestEngine(
    initial_capital=100000,        # Starting funds
    max_portfolio_exposure=0.50,   # Max 50% deployed
    max_position_size=0.10,        # Max 10% per position
    max_open_positions=5,          # Max 5 open trades
    risk_per_trade=0.02,           # Risk 2% per trade
    commission_percent=0.001       # 0.1% commission
)
```

### Customizable Parameters
- `initial_capital`: Portfolio size
- `max_portfolio_exposure`: Deployment limit
- `max_position_size`: Position concentration limit
- `max_open_positions`: Portfolio diversification limit
- `risk_per_trade`: Kelly Criterion risk
- `commission_percent`: Trade friction

---

## 📈 Output Examples

### Portfolio Snapshot Example
```
Date: 2024-01-05
  Cash: $85,000.00
  Open Positions: $12,000.00
  Closed P&L: $3,500.00
  Total Value: $100,500.00
  Open Positions: 2
  Closed Trades: 15
```

### Performance Metrics Example
```
Total Trades: 42
Winning Trades: 28 (66.7%)
Losing Trades: 14 (33.3%)

Profitability:
  Gross Wins: $18,500
  Gross Losses: -$8,000
  Profit Factor: 2.31

Returns:
  Net P&L: $10,500
  Total Return: 10.50%

Per Trade:
  Avg Winner: $660.71
  Avg Loser: -$571.43
  Avg Duration: 8.5 days
```

### Trade Log Example
```
Trade #1: AAPL
  Entry: 2024-01-01 @ $150.00 (66 shares)
  Exit: 2024-01-10 @ $162.00
  P&L: +$798.50 (8.07%)
  Duration: 9 days

Trade #2: TSLA
  Entry: 2024-01-05 @ $250.00 (40 shares)
  Exit: 2024-01-18 @ $245.00
  P&L: -$200.00 (-2.00%)
  Duration: 13 days
```

---

## 🔗 Integration Points

### With Phase 1 (Market Data)
- Input: Historical OHLC data
- Usage: Price lookups, historical backtesting

### With Phase 2 (Signal Engine)
- Input: Entry/exit signals, confidence, ATR
- Usage: Trade signals, position sizing

### With Phase 3 (Risk Engine)
- Input: Portfolio exposure limits, position sizing rules
- Usage: Constraint enforcement

### Standalone Usage
- Can test without other phases
- Mock data for development
- Validation of algorithms

---

## ✅ Feature Completeness Checklist

- [x] Trade opening with validation
- [x] Trade closing with P&L
- [x] Position sizing (Kelly)
- [x] Portfolio tracking
- [x] Mark-to-market updates
- [x] Portfolio snapshots
- [x] Performance metrics
- [x] Portfolio exposure limits
- [x] Multiple position handling
- [x] Drawdown tracking
- [x] Error handling
- [x] Edge case handling
- [x] Input validation
- [x] State validation

---

## 📚 Related Documentation

- [PHASE_4_BACKTESTING_INDEX.md](PHASE_4_BACKTESTING_INDEX.md) - Main guide
- [PHASE_4_BACKTESTING_CODE_REFERENCE.md](PHASE_4_BACKTESTING_CODE_REFERENCE.md) - Code examples
- [PHASE_4_BACKTESTING_TEST_GUIDE.md](PHASE_4_BACKTESTING_TEST_GUIDE.md) - Testing details
