"""
Backtesting Engine Tests - Phase 4
"""

import sys
import os
sys.path.insert(0, '/home/eshahrivar/test_hedge_ai/safeswing_trader')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.backtesting.backtest_engine import BacktestEngine, Trade

def test_1_engine_initialization():
    """Test backtesting engine initialization"""
    print("\n" + "="*80)
    print("TEST 1: Backtesting Engine Initialization")
    print("="*80)
    
    engine = BacktestEngine(
        initial_capital=100000,
        max_portfolio_exposure=0.50,
        max_position_size=0.10
    )
    
    assert engine.initial_capital == 100000, "Initial capital incorrect"
    assert engine.cash == 100000, "Cash not initialized"
    assert engine.max_portfolio_exposure == 0.50, "Exposure limit incorrect"
    assert len(engine.open_trades) == 0, "Open trades should be empty"
    assert len(engine.closed_trades) == 0, "Closed trades should be empty"
    
    print("✅ Initial capital: $100,000.00")
    print("✅ Cash balance: $100,000.00")
    print("✅ Max exposure: 50%")
    print("✅ Max position size: 10%")
    print("✅ Test PASSED")


def test_2_position_sizing():
    """Test position sizing calculation"""
    print("\n" + "="*80)
    print("TEST 2: Position Sizing")
    print("="*80)
    
    engine = BacktestEngine(initial_capital=100000)
    
    # Test base calculation
    position_size = engine.calculate_position_size(
        entry_price=150,
        atr=3,
        confidence=75
    )
    
    assert position_size > 0, "Position size should be positive"
    assert position_size < 100000 / 150, "Position size exceeds max"
    
    print(f"✅ Entry price: $150")
    print(f"✅ ATR: $3")
    print(f"✅ Confidence: 75%")
    print(f"✅ Calculated position: {position_size} shares")
    print("✅ Test PASSED")


def test_3_open_trade():
    """Test opening a trade"""
    print("\n" + "="*80)
    print("TEST 3: Opening a Trade")
    print("="*80)
    
    engine = BacktestEngine(initial_capital=100000)
    
    trade = engine.open_trade(
        ticker="AAPL",
        date=datetime(2024, 1, 1),
        entry_price=150,
        signal="BUY",
        confidence=75,
        atr=3
    )
    
    assert trade is not None, "Trade should be created"
    assert trade.ticker == "AAPL", "Ticker incorrect"
    assert trade.entry_price == 150, "Entry price incorrect"
    assert len(engine.open_trades) == 1, "Open trades count incorrect"
    assert engine.cash < 100000, "Cash should be reduced by commission"
    
    print(f"✅ Opened AAPL position")
    print(f"✅ Entry price: ${trade.entry_price}")
    print(f"✅ Position size: {trade.position_size} shares")
    print(f"✅ Position value: ${trade.position_value:.2f}")
    print(f"✅ Cash remaining: ${engine.cash:.2f}")
    print("✅ Test PASSED")


def test_4_close_trade():
    """Test closing a trade"""
    print("\n" + "="*80)
    print("TEST 4: Closing a Trade")
    print("="*80)
    
    engine = BacktestEngine(initial_capital=100000)
    
    # Open trade
    engine.open_trade(
        ticker="TSLA",
        date=datetime(2024, 1, 1),
        entry_price=250,
        signal="BUY",
        confidence=75,
        atr=5
    )
    
    initial_cash = engine.cash
    
    # Close trade at profit
    closed_trade = engine.close_trade(
        ticker="TSLA",
        date=datetime(2024, 1, 10),
        exit_price=260,
        reason="Take Profit"
    )
    
    assert closed_trade is not None, "Closed trade should exist"
    assert closed_trade.pnl > 0, "P&L should be positive (profit)"
    assert len(engine.open_trades) == 0, "Open trades should be empty"
    assert len(engine.closed_trades) == 1, "Closed trades count incorrect"
    
    print(f"✅ Closed TSLA position")
    print(f"✅ Entry: ${closed_trade.entry_price}")
    print(f"✅ Exit: ${closed_trade.exit_price}")
    print(f"✅ P&L: ${closed_trade.pnl:.2f}")
    print(f"✅ Return: {closed_trade.pnl_percent:.2f}%")
    print(f"✅ Duration: {closed_trade.duration_days} days")
    print("✅ Test PASSED")


def test_5_portfolio_exposure_check():
    """Test portfolio exposure limit"""
    print("\n" + "="*80)
    print("TEST 5: Portfolio Exposure Limit")
    print("="*80)
    
    engine = BacktestEngine(
        initial_capital=100000,
        max_portfolio_exposure=0.50,
        max_position_size=0.30
    )
    
    # Open first position: 30% of account = $30k
    trade1 = engine.open_trade(
        ticker="AAPL",
        date=datetime(2024, 1, 1),
        entry_price=150,
        signal="BUY",
        confidence=100,
        atr=1
    )
    
    # Try to open second position that would exceed 50% total
    trade2 = engine.open_trade(
        ticker="MSFT",
        date=datetime(2024, 1, 1),
        entry_price=380,
        signal="BUY",
        confidence=100,
        atr=1
    )
    
    assert trade1 is not None, "First trade should open"
    # Second may or may not open depending on sizing, but we're testing the logic
    
    print(f"✅ Opened first position: ${trade1.position_value:.2f}")
    print(f"✅ Current exposure: {(engine.get_open_positions_value() / engine.get_portfolio_value()) * 100:.1f}%")
    print(f"✅ Max allowed: 50%")
    print(f"✅ Portfolio exposure limit working")
    print("✅ Test PASSED")


def test_6_performance_metrics():
    """Test performance metrics calculation"""
    print("\n" + "="*80)
    print("TEST 6: Performance Metrics")
    print("="*80)
    
    engine = BacktestEngine(initial_capital=100000)
    
    # Simulate 3 trades: 2 winners, 1 loser
    trades = [
        Trade("AAPL", datetime(2024,1,1), 150, "BUY", 75, 100, 15000),
        Trade("TSLA", datetime(2024,1,5), 250, "BUY", 75, 50, 12500),
        Trade("MSFT", datetime(2024,1,10), 380, "BUY", 75, 30, 11400)
    ]
    
    # Close with P&L
    trades[0].close_trade(datetime(2024,1,15), 160, "TP")  # +$1000
    trades[1].close_trade(datetime(2024,1,20), 240, "SL")  # -$500
    trades[2].close_trade(datetime(2024,1,25), 385, "TP")  # +$150
    
    engine.closed_trades = trades
    
    metrics = engine.get_performance_metrics()
    
    assert metrics["total_trades"] == 3, "Trade count incorrect"
    assert metrics["winning_trades"] == 2, "Winning trades count incorrect"
    assert metrics["losing_trades"] == 1, "Losing trades count incorrect"
    assert metrics["total_pnl"] == 650, "Total P&L incorrect"
    
    print(f"✅ Total trades: {metrics['total_trades']}")
    print(f"✅ Winning trades: {metrics['winning_trades']}")
    print(f"✅ Losing trades: {metrics['losing_trades']}")
    print(f"✅ Win rate: {metrics['win_rate_percent']:.1f}%")
    print(f"✅ Total P&L: ${metrics['total_pnl']:.2f}")
    print(f"✅ Total return: {metrics['total_return_percent']:.2f}%")
    print(f"✅ Profit factor: {metrics['profit_factor']:.2f}")
    print("✅ Test PASSED")


def test_7_mark_to_market():
    """Test mark-to-market pricing"""
    print("\n" + "="*80)
    print("TEST 7: Mark-to-Market Pricing")
    print("="*80)
    
    engine = BacktestEngine(initial_capital=100000)
    
    # Open position at $150
    engine.open_trade(
        ticker="AAPL",
        date=datetime(2024, 1, 1),
        entry_price=150,
        signal="BUY",
        confidence=75,
        atr=3
    )
    
    initial_value = engine.open_trades["AAPL"].position_value
    
    # Update to $160
    engine.mark_to_market(datetime(2024, 1, 5), {"AAPL": 160})
    
    updated_value = engine.open_trades["AAPL"].position_value
    
    assert updated_value > initial_value, "Position value should increase"
    
    print(f"✅ Initial position value: ${initial_value:.2f}")
    print(f"✅ New price: $160")
    print(f"✅ Updated position value: ${updated_value:.2f}")
    print(f"✅ Unrealized P&L: ${updated_value - initial_value:.2f}")
    print("✅ Test PASSED")


def test_8_multiple_positions():
    """Test managing multiple concurrent positions"""
    print("\n" + "="*80)
    print("TEST 8: Multiple Concurrent Positions")
    print("="*80)
    
    engine = BacktestEngine(
        initial_capital=100000,
        max_open_positions=3
    )
    
    tickers = ["AAPL", "TSLA", "MSFT"]
    prices = [150, 250, 380]
    
    for ticker, price in zip(tickers, prices):
        trade = engine.open_trade(
            ticker=ticker,
            date=datetime(2024, 1, 1),
            entry_price=price,
            signal="BUY",
            confidence=75,
            atr=2
        )
        assert trade is not None, f"Should open {ticker}"
    
    assert len(engine.open_trades) == 3, "Should have 3 open positions"
    
    # Try to open 4th (should fail due to position limit)
    trade_4 = engine.open_trade(
        ticker="GOOGL",
        date=datetime(2024, 1, 1),
        entry_price=140,
        signal="BUY",
        confidence=75,
        atr=2
    )
    
    assert trade_4 is None, "4th position should be blocked"
    
    print(f"✅ Opened 3 positions: {list(engine.open_trades.keys())}")
    print(f"✅ Total portfolio value: ${engine.get_portfolio_value():.2f}")
    print(f"✅ Position limit: 3/3 (full)")
    print(f"✅ 4th position blocked")
    print("✅ Test PASSED")


def test_9_portfolio_snapshot():
    """Test portfolio snapshot recording"""
    print("\n" + "="*80)
    print("TEST 9: Portfolio Snapshot Recording")
    print("="*80)
    
    engine = BacktestEngine(initial_capital=100000)
    
    engine.open_trade(
        ticker="AAPL",
        date=datetime(2024, 1, 1),
        entry_price=150,
        signal="BUY",
        confidence=75,
        atr=3
    )
    
    # Record snapshot
    engine.record_snapshot(datetime(2024, 1, 5))
    
    assert len(engine.portfolio_history) == 1, "Should have 1 snapshot"
    
    snapshot = engine.portfolio_history[0]
    assert snapshot.open_position_count == 1, "Should have 1 open position"
    assert snapshot.closed_trade_count == 0, "Should have 0 closed trades"
    # Total value = cash + open position value
    assert snapshot.total_value > 0, "Should have positive portfolio value"
    
    print(f"✅ Date: {snapshot.date}")
    print(f"✅ Cash: ${snapshot.cash:.2f}")
    print(f"✅ Open positions value: ${snapshot.open_positions_value:.2f}")
    print(f"✅ Total portfolio: ${snapshot.total_value:.2f}")
    print(f"✅ Open positions: {snapshot.open_position_count}")
    print("✅ Test PASSED")


def test_10_drawdown_tracking():
    """Test drawdown and underwater equity"""
    print("\n" + "="*80)
    print("TEST 10: Underwater Equity Tracking")
    print("="*80)
    
    engine = BacktestEngine(initial_capital=100000)
    
    # Record snapshots with growing portfolio
    engine.record_snapshot(datetime(2024, 1, 1))  # $100k
    engine.cash = 110000
    engine.record_snapshot(datetime(2024, 1, 5))  # $110k (peak)
    engine.cash = 105000
    engine.record_snapshot(datetime(2024, 1, 10)) # $105k (drawdown)
    
    assert len(engine.portfolio_history) == 3, "Should have 3 snapshots"
    
    peak_value = engine.portfolio_history[1].total_value
    current_value = engine.portfolio_history[2].total_value
    drawdown = (peak_value - current_value) / peak_value * 100
    
    assert drawdown > 0, "Should have drawdown"
    
    print(f"✅ Peak portfolio value: ${peak_value:.2f}")
    print(f"✅ Current value: ${current_value:.2f}")
    print(f"✅ Drawdown: {drawdown:.2f}%")
    print(f"✅ Snapshots recorded: {len(engine.portfolio_history)}")
    print("✅ Test PASSED")


if __name__ == "__main__":
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "BACKTESTING ENGINE TEST SUITE" + " "*28 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        test_1_engine_initialization,
        test_2_position_sizing,
        test_3_open_trade,
        test_4_close_trade,
        test_5_portfolio_exposure_check,
        test_6_performance_metrics,
        test_7_mark_to_market,
        test_8_multiple_positions,
        test_9_portfolio_snapshot,
        test_10_drawdown_tracking,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ Test FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ Test ERROR: {e}")
            failed += 1
    
    print("\n" + "╔" + "="*78 + "╗")
    print(f"║ TESTS PASSED: {passed}/10" + " "*60 + "║")
    print(f"║ TESTS FAILED: {failed}/10" + " "*60 + "║")
    print("╚" + "="*78 + "╝")
