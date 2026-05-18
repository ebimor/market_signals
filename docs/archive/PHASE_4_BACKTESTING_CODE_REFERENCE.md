# Phase 4 Backtesting Engine - Code Reference

**Full Code Examples and Implementation Details**

---

## Complete Initialization Example

```python
from backend.backtesting.backtest_engine import BacktestEngine
from datetime import datetime

# Create engine with custom parameters
engine = BacktestEngine(
    initial_capital=100000,           # Starting capital
    max_portfolio_exposure=0.50,      # Max 50% deployed (from Phase 3)
    max_position_size=0.10,           # Max 10% per position
    max_open_positions=5,             # Max 5 concurrent trades
    risk_per_trade=0.02,              # Risk 2% per trade
    commission_percent=0.001          # 0.1% commission
)

# Verify initialization
print(f"Starting Capital: ${engine.initial_capital:,.2f}")
print(f"Cash Available: ${engine.cash:,.2f}")
print(f"Portfolio Value: ${engine.get_portfolio_value():,.2f}")
```

---

## Opening a Trade

### Example 1: Simple BUY Signal

```python
# When your Signal Engine generates a BUY signal
trade = engine.open_trade(
    ticker="AAPL",
    date=datetime(2024, 1, 15),
    entry_price=150.25,
    signal="BUY",
    confidence=75,  # 75% confident in this trade
    atr=3.50        # Average True Range for position sizing
)

if trade:
    print(f"✅ Opened AAPL position")
    print(f"   Entry: ${trade.entry_price}")
    print(f"   Shares: {trade.position_size}")
    print(f"   Value: ${trade.position_value:,.2f}")
    print(f"   Cash after: ${engine.cash:,.2f}")
else:
    print("❌ Could not open trade (constraints violated)")
```

**What Happens Inside**:
1. Validates position constraints
   - Not at max open positions limit (5)
   - Not at max portfolio exposure (50%)
   - Have sufficient cash

2. Calculates position size using Kelly Criterion:
   ```
   position_size = (100000 * 0.02) / (150.25 * 3.50) * 0.75
                 = 66 shares
   ```

3. Commits cash and creates Trade object
4. Returns Trade object or None if failed

### Example 2: Multiple Signals

```python
# Portfolio allocation strategy
signals = [
    {"ticker": "AAPL", "price": 150, "confidence": 75, "atr": 3},
    {"ticker": "MSFT", "price": 380, "confidence": 80, "atr": 4},
    {"ticker": "TSLA", "price": 250, "confidence": 70, "atr": 5},
]

for signal in signals:
    trade = engine.open_trade(
        ticker=signal["ticker"],
        date=datetime(2024, 1, 15),
        entry_price=signal["price"],
        signal="BUY",
        confidence=signal["confidence"],
        atr=signal["atr"]
    )
    
    if trade:
        print(f"✅ {signal['ticker']}: {trade.position_size} shares")
    else:
        print(f"❌ {signal['ticker']}: Could not open")

print(f"\nOpen positions: {len(engine.open_trades)}")
print(f"Portfolio exposure: {engine.get_portfolio_exposure()}%")
```

---

## Closing a Trade

### Example 1: Take Profit

```python
# Close with profit
closed_trade = engine.close_trade(
    ticker="AAPL",
    date=datetime(2024, 1, 25),
    exit_price=162.50,
    reason="Take Profit"
)

if closed_trade:
    print(f"✅ Closed AAPL")
    print(f"   Entry: ${closed_trade.entry_price}")
    print(f"   Exit: ${closed_trade.exit_price}")
    print(f"   P&L: ${closed_trade.pnl:,.2f}")
    print(f"   Return: {closed_trade.pnl_percent:.2f}%")
    print(f"   Duration: {closed_trade.duration_days} days")
    print(f"   Cash now: ${engine.cash:,.2f}")
```

**Calculation**:
- Shares: 66
- Entry: $150.25
- Exit: $162.50
- Gross P&L: (162.50 - 150.25) × 66 = $808.50
- Minus commission: $808.50 - $10 = **$798.50**
- Return: ($798.50 / $9900) = 8.07%

### Example 2: Stop Loss

```python
# Close at stop loss
closed_trade = engine.close_trade(
    ticker="TSLA",
    date=datetime(2024, 1, 18),
    exit_price=245.00,
    reason="Stop Loss"
)

if closed_trade and closed_trade.pnl < 0:
    print(f"⚠️  Stopped out on TSLA")
    print(f"   Loss: ${closed_trade.pnl:,.2f}")
```

### Example 3: Close All Positions

```python
# End of day - close all open positions
current_prices = {
    "AAPL": 162,
    "MSFT": 385,
    "TSLA": 248
}

for ticker, price in current_prices.items():
    if ticker in engine.open_trades:
        engine.close_trade(
            ticker=ticker,
            date=datetime(2024, 1, 25),
            exit_price=price,
            reason="EOD Close"
        )

print(f"Open positions: {len(engine.open_trades)}")
print(f"Closed trades: {len(engine.closed_trades)}")
```

---

## Mark-to-Market Updates

### Daily Price Updates

```python
# Update portfolio with latest prices
daily_prices = {
    "AAPL": 162.50,
    "MSFT": 385.75,
    "TSLA": 248.30
}

engine.mark_to_market(datetime(2024, 1, 16), daily_prices)

# Check unrealized P&L
for ticker, trade in engine.open_trades.items():
    unrealized_pnl = (trade.position_value - 
                      (trade.position_size * trade.entry_price))
    print(f"{ticker}: ${unrealized_pnl:,.2f} unrealized")
```

**Impact**:
- Updates `position_value` for each open trade
- Enables mark-to-market P&L tracking
- Used for portfolio snapshot

---

## Portfolio Snapshots

### Recording State

```python
# Record portfolio state at end of each day
engine.record_snapshot(datetime(2024, 1, 16))

# Later, review history
for snapshot in engine.portfolio_history:
    print(f"\n{snapshot.date.strftime('%Y-%m-%d')}")
    print(f"  Cash: ${snapshot.cash:,.2f}")
    print(f"  Open Positions: ${snapshot.open_positions_value:,.2f}")
    print(f"  Closed P&L: ${snapshot.closed_trades_value:,.2f}")
    print(f"  Total Value: ${snapshot.total_value:,.2f}")
    print(f"  Open Trades: {snapshot.open_position_count}")
```

### Equity Curve

```python
# Build equity curve from snapshots
dates = []
equity_values = []

for snapshot in engine.portfolio_history:
    dates.append(snapshot.date)
    equity_values.append(snapshot.total_value)

# Calculate returns and drawdown
starting_value = engine.initial_capital
peak_value = max(equity_values)
current_value = equity_values[-1]

total_return = (current_value - starting_value) / starting_value * 100
max_drawdown = (peak_value - min(equity_values)) / peak_value * 100

print(f"Return: {total_return:.2f}%")
print(f"Max Drawdown: {max_drawdown:.2f}%")
```

---

## Performance Metrics

### Complete Example

```python
# Simulate trading for the month
trades_data = [
    # Trade 1: Winner
    {"entry": 150, "exit": 160, "shares": 66},
    # Trade 2: Loser
    {"entry": 250, "exit": 245, "shares": 40},
    # Trade 3: Winner
    {"entry": 380, "exit": 390, "shares": 26},
]

# Calculate metrics
metrics = engine.get_performance_metrics()

print("=" * 50)
print("STRATEGY PERFORMANCE")
print("=" * 50)
print(f"\nTrade Summary:")
print(f"  Total Trades: {metrics['total_trades']}")
print(f"  Winning Trades: {metrics['winning_trades']}")
print(f"  Losing Trades: {metrics['losing_trades']}")
print(f"  Win Rate: {metrics['win_rate_percent']:.1f}%")

print(f"\nProfitability:")
print(f"  Gross Wins: ${metrics['gross_wins']:,.2f}")
print(f"  Gross Losses: ${abs(metrics['gross_losses']):,.2f}")
print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
print(f"  Net P&L: ${metrics['total_pnl']:,.2f}")
print(f"  Total Return: {metrics['total_return_percent']:.2f}%")

print(f"\nPer-Trade Stats:")
print(f"  Avg Winner: ${metrics['avg_winner']:,.2f}")
print(f"  Avg Loser: ${metrics['avg_loser']:,.2f}")
print(f"  Largest Win: ${metrics['largest_win']:,.2f}")
print(f"  Largest Loss: ${metrics['largest_loss']:,.2f}")

print(f"\nTrade Duration:")
print(f"  Avg Days: {metrics['avg_duration_days']:.1f}")
```

**Output Example**:
```
==================================================
STRATEGY PERFORMANCE
==================================================

Trade Summary:
  Total Trades: 42
  Winning Trades: 28
  Losing Trades: 14
  Win Rate: 66.7%

Profitability:
  Gross Wins: $18,500.00
  Gross Losses: -$8,000.00
  Profit Factor: 2.31
  Net P&L: $10,500.00
  Total Return: 10.50%

Per-Trade Stats:
  Avg Winner: $660.71
  Avg Loser: -$571.43
  Largest Win: $2,100.00
  Largest Loss: -$1,200.00

Trade Duration:
  Avg Days: 8.5
```

---

## Advanced: Portfolio Exposure

### Checking Exposure

```python
# From Phase 3 integration
exposure = engine.calculate_portfolio_exposure()

print(f"Current Exposure: {exposure['current_exposure']:.1f}%")
print(f"Capacity: {exposure['remaining_capacity']:.1f}%")
print(f"At Limit: {exposure['at_limit']}")

# Before opening a new trade
if exposure['remaining_capacity'] < 15:  # Need 15% capacity
    print("⚠️  Not enough capacity for new trade")
```

### Exposure-Aware Position Sizing

```python
# Automatically adjust for exposure limits
base_size = engine.calculate_position_size(150, 3, 75)
adjusted_size = engine.adjust_position_size_for_exposure(base_size)

print(f"Base size: {base_size} shares")
print(f"After exposure limit: {adjusted_size} shares")
print(f"Reduction: {(base_size - adjusted_size) / base_size * 100:.1f}%")
```

---

## Integration with Signal Engine

```python
# Example workflow
from backend.signals.signal_engine import SignalEngine

signal_engine = SignalEngine()
backtest_engine = BacktestEngine(initial_capital=100000)

# For each trading day
for date in trading_dates:
    # Get signals from Phase 2
    signals = signal_engine.generate_signals(date)
    
    # Execute trades based on signals
    for signal in signals:
        if signal["action"] == "BUY":
            trade = backtest_engine.open_trade(
                ticker=signal["ticker"],
                date=date,
                entry_price=signal["price"],
                signal="BUY",
                confidence=signal["confidence"],
                atr=signal["atr"]
            )
        elif signal["action"] == "SELL":
            trade = backtest_engine.close_trade(
                ticker=signal["ticker"],
                date=date,
                exit_price=signal["price"],
                reason="Signal"
            )
    
    # Update market prices
    backtest_engine.mark_to_market(date, daily_prices[date])
    
    # Record state
    backtest_engine.record_snapshot(date)

# Analyze results
metrics = backtest_engine.get_performance_metrics()
```

---

## Error Handling

```python
# Trade opening might fail
try:
    trade = engine.open_trade(
        ticker="AAPL",
        date=datetime(2024, 1, 15),
        entry_price=150,
        signal="BUY",
        confidence=75,
        atr=3
    )
    
    if trade is None:
        print("Trade not opened - constraints violated")
        print(f"  Open positions: {len(engine.open_trades)}/{engine.max_open_positions}")
        print(f"  Exposure: {engine.calculate_portfolio_exposure()}")
        print(f"  Cash: ${engine.cash:,.2f}")
    else:
        print(f"✅ Trade opened: {trade.position_size} shares")
        
except Exception as e:
    print(f"Error: {e}")

# Trade closing might fail if not found
try:
    closed = engine.close_trade(
        ticker="NONEXISTENT",
        date=datetime(2024, 1, 20),
        exit_price=160,
        reason="Manual"
    )
    
    if closed is None:
        print("Trade not found")
        print(f"Open positions: {list(engine.open_trades.keys())}")
        
except Exception as e:
    print(f"Error: {e}")
```

---

## Testing

```python
# From test suite
def test_complete_trade_cycle():
    """Complete open-close cycle"""
    engine = BacktestEngine(initial_capital=100000)
    
    # Open
    trade = engine.open_trade(
        ticker="AAPL",
        date=datetime(2024, 1, 1),
        entry_price=150,
        signal="BUY",
        confidence=75,
        atr=3
    )
    assert trade is not None
    assert len(engine.open_trades) == 1
    
    # Update price
    engine.mark_to_market(datetime(2024, 1, 5), {"AAPL": 160})
    
    # Close
    closed = engine.close_trade(
        ticker="AAPL",
        date=datetime(2024, 1, 10),
        exit_price=162,
        reason="Take Profit"
    )
    assert closed is not None
    assert closed.pnl > 0
    assert len(engine.open_trades) == 0
    assert len(engine.closed_trades) == 1
    
    print("✅ Complete trade cycle passed")
```

---

## Performance Optimization

```python
# For backtesting large date ranges
# Pre-allocate arrays if possible
snapshots = []
trade_count = 0

# Batch operations
for date in date_range:
    # Collect all actions for the day
    closes = []
    opens = []
    
    # Process closes first (free up capital)
    for close_action in closes:
        engine.close_trade(**close_action)
    
    # Process opens (use freed capital)
    for open_action in opens:
        engine.open_trade(**open_action)
    
    # Single price update
    engine.mark_to_market(date, daily_prices[date])
    
    # Record snapshot
    snapshots.append(engine.record_snapshot(date))

# Calculate final metrics once
final_metrics = engine.get_performance_metrics()
```

---

## All Code Files

- **Engine**: [backend/backtesting/backtest_engine.py](../backend/backtesting/backtest_engine.py)
- **Tests**: [backend/backtesting/test_backtest_engine.py](../backend/backtesting/test_backtest_engine.py)
