#!/usr/bin/env python3
"""
Trading API Usage Examples

Complete guide for using the Trading API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"
TRADING_API = f"{BASE_URL}/api/trading"

print()
print("="*70)
print("SafeSwing Trader - Trading API Examples")
print("="*70)
print()

# ============================================================================
# EXAMPLE 1: Get System Status
# ============================================================================

print("1️⃣  GET SYSTEM STATUS")
print("-" * 70)

response = requests.get(f"{TRADING_API}/status")
print(f"curl {TRADING_API}/status")
print()
print(json.dumps(response.json(), indent=2))
print()

# ============================================================================
# EXAMPLE 2: Generate Trading Signals
# ============================================================================

print("2️⃣  GENERATE TRADING SIGNALS")
print("-" * 70)

signal_data = {
    "symbol": "AAPL",
    "signal_type": "BUY",
    "price": 150.25,
    "confidence": 75,
    "reason": "MACD Bull + RSI 45 + Price>SMA20",
    "position_size": 100,
    "stop_loss": 148.00,
    "take_profit": 155.00
}

print("POST /api/trading/signals")
print(json.dumps(signal_data, indent=2))
print()

response = requests.post(f"{TRADING_API}/signals", json=signal_data)
signal = response.json()
signal_id = signal["signal_id"]

print("Response:")
print(json.dumps(signal, indent=2))
print()

# ============================================================================
# EXAMPLE 3: Get Pending Signals
# ============================================================================

print("3️⃣  GET PENDING SIGNALS")
print("-" * 70)

print(f"curl {TRADING_API}/signals")
print()

response = requests.get(f"{TRADING_API}/signals")
signals = response.json()

print(f"Found {len(signals)} pending signals:")
for sig in signals:
    print(f"  - {sig['signal_id']}: {sig['symbol']} {sig['type']} @ ${sig['price']}")
print()

# ============================================================================
# EXAMPLE 4: Approve a Trade
# ============================================================================

print("4️⃣  APPROVE A TRADE")
print("-" * 70)

approval_data = {
    "signal_id": signal_id,
    "approval_notes": "Looks good, execute as suggested",
    "modified_position_size": None,
    "modified_stop_loss": None,
    "modified_take_profit": None
}

print("POST /api/trading/approve")
print(json.dumps(approval_data, indent=2))
print()

response = requests.post(f"{TRADING_API}/approve", json=approval_data)
print("Response:")
print(json.dumps(response.json(), indent=2))
print()

# ============================================================================
# EXAMPLE 5: Execute Approved Trade
# ============================================================================

print("5️⃣  EXECUTE TRADE")
print("-" * 70)

execution_data = {"signal_id": signal_id}

print("POST /api/trading/execute")
print(json.dumps(execution_data, indent=2))
print()

response = requests.post(f"{TRADING_API}/execute", json=execution_data)
trade = response.json()
trade_id = trade["trade_id"]

print("Response:")
print(json.dumps(trade, indent=2))
print()

# ============================================================================
# EXAMPLE 6: Get Open Trades
# ============================================================================

print("6️⃣  GET OPEN TRADES")
print("-" * 70)

print(f"curl {TRADING_API}/trades/open")
print()

response = requests.get(f"{TRADING_API}/trades/open")
trades = response.json()

print(f"Found {len(trades)} open trades:")
for t in trades:
    print(f"  - {t['trade_id']}: {t['symbol']} @ ${t['entry_price']}")
print()

# ============================================================================
# EXAMPLE 7: Close a Trade
# ============================================================================

print("7️⃣  CLOSE TRADE")
print("-" * 70)

close_data = {
    "trade_id": trade_id,
    "exit_price": 155.00,
    "exit_reason": "Take profit reached"
}

print("POST /api/trading/close")
print(json.dumps(close_data, indent=2))
print()

response = requests.post(f"{TRADING_API}/close", json=close_data)
result = response.json()

print("Response:")
print(json.dumps(result, indent=2))
print()

# ============================================================================
# EXAMPLE 8: Get Trade History
# ============================================================================

print("8️⃣  GET TRADE HISTORY")
print("-" * 70)

print(f"curl {TRADING_API}/trades/history")
print()

response = requests.get(f"{TRADING_API}/trades/history")
history = response.json()

print(f"Found {len(history)} closed trades:")
for t in history:
    status = "✅" if t["pnl"] and t["pnl"] > 0 else "❌"
    print(f"  {status} {t['trade_id']}: P&L ${t['pnl']:,.2f}")
print()

# ============================================================================
# EXAMPLE 9: Get Performance Stats
# ============================================================================

print("9️⃣  GET PERFORMANCE STATS")
print("-" * 70)

print(f"curl {TRADING_API}/stats")
print()

response = requests.get(f"{TRADING_API}/stats")
stats = response.json()

print("Response:")
print(json.dumps(stats, indent=2))
print()

# ============================================================================
# EXAMPLE 10: Get Complete Dashboard
# ============================================================================

print("🔟 GET DASHBOARD")
print("-" * 70)

print(f"curl {TRADING_API}/dashboard")
print()

response = requests.get(f"{TRADING_API}/dashboard")
dashboard = response.json()

print("Dashboard Summary:")
print(f"  Pending signals: {len(dashboard['pending_signals'])}")
print(f"  Open trades: {len(dashboard['open_trades'])}")
print(f"  Trade history: {len(dashboard['trade_history'])}")
print(f"  Performance: {dashboard['performance']}")
print()

print("="*70)
print("✅ API Examples Complete")
print("="*70)
print()
print("FULL WORKFLOW:")
print("  1. POST /api/trading/signals       - Generate signal")
print("  2. GET  /api/trading/signals       - View pending")
print("  3. POST /api/trading/approve       - User approves")
print("  4. POST /api/trading/execute       - Trade executes")
print("  5. GET  /api/trading/trades/open   - Monitor position")
print("  6. POST /api/trading/close         - Close trade")
print("  7. GET  /api/trading/stats         - View performance")
print()
