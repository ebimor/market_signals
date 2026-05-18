#!/usr/bin/env python3
"""
Manual Trade Approval Workflow Example

Demonstrates how to use TradeManager for manual trade confirmation:
1. Generate signals (suggestions)
2. Review pending signals
3. Approve/reject/modify trades
4. Execute approved trades
5. Monitor and close trades
6. View performance
"""

from backend.trading.trade_manager import TradeManager, SignalType
import json

print()
print("="*70)
print("SafeSwing Trader - Manual Trade Approval System")
print("="*70)
print()

# Initialize trade manager
tm = TradeManager()

# ==============================================================================
# WORKFLOW EXAMPLE
# ==============================================================================

print("WORKFLOW: Generate Signal → Review → Approve → Execute → Track → Close")
print()

# Step 1: Strategy generates signals (suggestions for user review)
print("1️⃣  GENERATE SIGNALS")
print("-" * 70)

sig_aapl = tm.add_signal(
    symbol="AAPL",
    signal_type=SignalType.BUY,
    price=150.25,
    confidence=75,
    reason="MACD Bull + RSI 45",
    position_size=100,
    stop_loss=148.00,
    take_profit=155.00
)

sig_tsla = tm.add_signal(
    symbol="TSLA",
    signal_type=SignalType.BUY,
    price=250.50,
    confidence=65,
    reason="Golden Cross",
    position_size=50,
    stop_loss=245.00,
    take_profit=260.00
)

print(f"✅ Generated {len(tm.get_pending_signals())} trading signals")
print()

# Step 2: Show signals for user review
print("2️⃣  REVIEW SIGNALS")
print("-" * 70)

signals = tm.get_pending_signals()
for i, sig in enumerate(signals, 1):
    print(f"\nSignal #{i}: {sig['symbol']} {sig['type']}")
    print(f"  Entry Price:    ${sig['price']}")
    print(f"  Confidence:     {sig['confidence']}%")
    print(f"  Position:       {sig['position_size']} shares")
    print(f"  Stop Loss:      ${sig['stop_loss']}")
    print(f"  Take Profit:    ${sig['take_profit']}")
    print(f"  Reason:         {sig['reason']}")

print()
print("📋 You review these signals and decide to approve/reject")
print()

# Step 3: User approves/rejects
print("3️⃣  APPROVE/REJECT")
print("-" * 70)

tm.approve_trade(sig_aapl.signal_id, approval_notes="Approve as suggested")
print(f"✅ Approved AAPL")

tm.approve_trade(
    sig_tsla.signal_id,
    approval_notes="Reduce position size",
    modified_position_size=30  # User adjusts from 50 to 30
)
print(f"✅ Approved TSLA (adjusted position: 50→30 shares)")
print()

# Step 4: Execute approved trades
print("4️⃣  EXECUTE TRADES")
print("-" * 70)

trade1 = tm.execute_trade(sig_aapl.signal_id)
trade2 = tm.execute_trade(sig_tsla.signal_id)

print(f"✅ Executed: {trade1.trade_id} (AAPL)")
print(f"✅ Executed: {trade2.trade_id} (TSLA)")
print()

# Step 5: Monitor open trades
print("5️⃣  MONITOR OPEN TRADES")
print("-" * 70)

open_trades = tm.get_open_trades()
for trade in open_trades:
    profit_at_tp = (trade['take_profit'] - trade['entry_price']) * trade['position_size']
    print(f"\n{trade['trade_id']}")
    print(f"  Entry:  ${trade['entry_price']} x {trade['position_size']} shares")
    print(f"  Stop:   ${trade['stop_loss']} | TP: ${trade['take_profit']}")
    print(f"  Profit at TP: ${profit_at_tp:,.2f}")
print()

# Step 6: Close trades (when TP/SL hit)
print("6️⃣  CLOSE TRADES (TP/SL Hit)")
print("-" * 70)

tm.close_trade(
    trade_id=trade1.trade_id,
    exit_price=155.00,
    exit_reason="Take profit reached"
)
print(f"✅ AAPL: Closed at take profit ($155.00)")

tm.close_trade(
    trade_id=trade2.trade_id,
    exit_price=245.00,
    exit_reason="Stop loss hit"
)
print(f"❌ TSLA: Closed at stop loss ($245.00)")
print()

# Step 7: View performance
print("7️⃣  PERFORMANCE SUMMARY")
print("-" * 70)

history = tm.get_trade_history()
for trade in history:
    result = "✅ WIN" if trade['pnl'] > 0 else "❌ LOSS"
    print(f"\n{result}: {trade['trade_id']}")
    print(f"  Entry: ${trade['entry_price']} → Exit: ${trade['exit_price']}")
    print(f"  P&L:   ${trade['pnl']:,.2f} ({trade['pnl_percent']:+.2f}%)")

stats = tm.get_performance_stats()
print()
print("📊 Statistics:")
print(f"  Total Trades: {stats['total_trades']}")
print(f"  Win Rate:     {stats['win_rate']:.1f}%")
print(f"  Total P&L:    ${stats['total_pnl']:,.2f}")
print()

print("="*70)
print("✅ Manual Approval Workflow Complete")
print("="*70)
print()
print("Key Benefits:")
print("  ✓ No automatic trades - you always decide")
print("  ✓ Review all signals before execution")
print("  ✓ Modify position size/SL/TP if needed")
print("  ✓ All trades tracked with P&L")
print("  ✓ Performance statistics")
print("  ✓ Trade records saved")
print()
