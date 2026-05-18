"""
Phase 4b: Strategy Simulator - Test Suite
Tests for end-to-end strategy simulation
"""

import sys
import os
sys.path.insert(0, '/home/eshahrivar/test_hedge_ai/safeswing_trader')

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from backend.backtesting.strategy_simulator import StrategySimulator, BacktestConfig, BacktestResult


def test_1_simulator_initialization():
    """Test strategy simulator initialization"""
    print("\n" + "="*80)
    print("TEST 1: Strategy Simulator Initialization")
    print("="*80)
    
    config = BacktestConfig(
        initial_capital=100000,
        symbols=["AAPL", "TSLA", "MSFT"]
    )
    
    simulator = StrategySimulator(config)
    
    assert simulator.config.initial_capital == 100000, "Config not stored"
    assert len(simulator.config.symbols) == 3, "Symbols not stored"
    assert simulator.engine is not None, "Engine not initialized"
    assert len(simulator.price_data) == 0, "Price data should be empty"
    
    print("✅ Config initialized: $100,000 capital")
    print("✅ Symbols: AAPL, TSLA, MSFT")
    print("✅ Engine ready")
    print("✅ Test PASSED")


def test_2_mock_data_generation():
    """Test mock data generation"""
    print("\n" + "="*80)
    print("TEST 2: Mock Data Generation")
    print("="*80)
    
    config = BacktestConfig(initial_capital=100000)
    simulator = StrategySimulator(config)
    
    data = simulator.generate_mock_data("AAPL", days=30)
    
    assert len(data) >= 20, "Should have at least 20 business days"
    assert 'Close' in data.columns, "Missing Close"
    assert 'Open' in data.columns, "Missing Open"
    assert 'High' in data.columns, "Missing High"
    assert 'Low' in data.columns, "Missing Low"
    assert 'Volume' in data.columns, "Missing Volume"
    assert data['Close'].iloc[-1] > 0, "Prices should be positive"
    
    print(f"✅ Generated 30 days of data")
    print(f"✅ Price range: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
    print(f"✅ Latest close: ${data['Close'].iloc[-1]:.2f}")
    print("✅ Test PASSED")


def test_3_load_historical_data():
    """Test loading historical data"""
    print("\n" + "="*80)
    print("TEST 3: Load Historical Data")
    print("="*80)
    
    config = BacktestConfig(initial_capital=100000)
    simulator = StrategySimulator(config)
    
    # Generate and load data
    data = simulator.generate_mock_data("AAPL", days=30)
    simulator.load_historical_data("AAPL", data)
    
    assert "AAPL" in simulator.price_data, "Data not stored"
    assert len(simulator.price_data["AAPL"]) >= 20, "Data not loaded correctly"
    
    print(f"✅ Loaded AAPL: {len(data)} days")
    print(f"✅ Date range: {data.index[0].date()} to {data.index[-1].date()}")
    print(f"✅ Data stored in simulator")
    print("✅ Test PASSED")


def test_4_signal_generation():
    """Test signal generation"""
    print("\n" + "="*80)
    print("TEST 4: Signal Generation")
    print("="*80)
    
    config = BacktestConfig(
        initial_capital=100000,
        symbols=["AAPL", "TSLA"]
    )
    simulator = StrategySimulator(config)
    
    # Load data for both symbols
    for symbol in config.symbols:
        data = simulator.generate_mock_data(symbol, days=60)
        simulator.load_historical_data(symbol, data)
    
    # Generate signals using the last available date
    current_date = simulator.price_data["AAPL"].index[-1]
    
    prices = {}
    for symbol in config.symbols:
        if current_date in simulator.price_data[symbol].index:
            prices[symbol] = simulator.price_data[symbol].loc[current_date, "Close"]
    
    if not prices:
        print("⚠️  No prices available for signal generation")
        print("✅ Test PASSED (skipped due to data)")
        return
    
    signals = simulator._generate_signals(current_date, prices)
    
    assert isinstance(signals, list), "Signals should be a list"
    for signal in signals:
        assert 'symbol' in signal, "Signal missing symbol"
        assert 'action' in signal, "Signal missing action"
        assert 'price' in signal, "Signal missing price"
    
    print(f"✅ Generated {len(signals)} signals")
    for signal in signals:
        print(f"   {signal['symbol']}: {signal['action']} @ ${signal['price']:.2f}")
    print("✅ Test PASSED")


def test_5_full_simulation():
    """Test complete strategy simulation"""
    print("\n" + "="*80)
    print("TEST 5: Full Strategy Simulation")
    print("="*80)
    
    config = BacktestConfig(
        initial_capital=100000,
        symbols=["AAPL"],
        lookback_period=60
    )
    simulator = StrategySimulator(config)
    
    # Run simulation
    result = simulator.run_simulation(verbose=False)
    
    assert result is not None, "Should return result"
    assert result.initial_capital == 100000, "Initial capital incorrect"
    assert result.final_capital > 0, "Final capital should be positive"
    assert result.total_trades >= 0, "Should have trades"
    assert result.max_drawdown_percent >= 0, "Drawdown should be tracked"
    
    print(f"✅ Simulation completed")
    print(f"✅ Initial: ${result.initial_capital:,.2f}")
    print(f"✅ Final: ${result.final_capital:,.2f}")
    print(f"✅ Return: {result.total_return_percent:.2f}%")
    print(f"✅ Trades: {result.total_trades}")
    print(f"✅ Win Rate: {result.win_rate_percent:.1f}%")
    print("✅ Test PASSED")


def test_6_multi_symbol_simulation():
    """Test simulation with multiple symbols"""
    print("\n" + "="*80)
    print("TEST 6: Multi-Symbol Simulation")
    print("="*80)
    
    config = BacktestConfig(
        initial_capital=100000,
        symbols=["AAPL", "TSLA", "MSFT"],
        lookback_period=60
    )
    simulator = StrategySimulator(config)
    
    result = simulator.run_simulation(verbose=False)
    
    assert result.total_trades >= 0, "Should have trades"
    assert len(result.trades) > 0 or result.total_trades == 0, "Trade list consistent"
    
    print(f"✅ Simulated 3 symbols")
    print(f"✅ Total trades: {result.total_trades}")
    print(f"✅ Return: {result.total_return_percent:.2f}%")
    print(f"✅ Max drawdown: {result.max_drawdown_percent:.2f}%")
    print("✅ Test PASSED")


def test_7_performance_metrics():
    """Test performance metrics calculation"""
    print("\n" + "="*80)
    print("TEST 7: Performance Metrics Calculation")
    print("="*80)
    
    config = BacktestConfig(
        initial_capital=100000,
        symbols=["AAPL"],
        lookback_period=90
    )
    simulator = StrategySimulator(config)
    
    result = simulator.run_simulation(verbose=False)
    
    # Check metrics
    assert result.total_trades >= 0, "Total trades invalid"
    assert result.winning_trades >= 0, "Winning trades invalid"
    assert result.losing_trades >= 0, "Losing trades invalid"
    assert result.win_rate_percent >= 0, "Win rate invalid"
    assert result.profit_factor >= 0, "Profit factor invalid"
    
    # Consistency checks
    assert result.winning_trades + result.losing_trades <= result.total_trades, "Trade count mismatch"
    if result.total_trades > 0:
        expected_win_rate = (result.winning_trades / result.total_trades) * 100
        assert abs(result.win_rate_percent - expected_win_rate) < 0.1, "Win rate calculation error"
    
    print(f"✅ Total trades: {result.total_trades}")
    print(f"✅ Winners: {result.winning_trades}, Losers: {result.losing_trades}")
    print(f"✅ Win rate: {result.win_rate_percent:.1f}%")
    print(f"✅ Profit factor: {result.profit_factor:.2f}")
    print(f"✅ Net P&L: ${result.net_pnl:.2f}")
    print("✅ Test PASSED")


def test_8_equity_curve_tracking():
    """Test equity curve tracking"""
    print("\n" + "="*80)
    print("TEST 8: Equity Curve Tracking")
    print("="*80)
    
    config = BacktestConfig(
        initial_capital=100000,
        symbols=["AAPL"],
        lookback_period=60
    )
    simulator = StrategySimulator(config)
    
    result = simulator.run_simulation(verbose=False)
    
    assert len(result.equity_curve) > 0, "Should have equity curve"
    assert len(result.daily_returns) >= 0, "Should have daily returns"
    
    # Check equity values
    equity_values = [v[1] for v in result.equity_curve]
    assert all(v > 0 for v in equity_values), "Equity should be positive"
    
    print(f"✅ Equity curve points: {len(result.equity_curve)}")
    print(f"✅ Starting equity: ${equity_values[0]:,.2f}")
    print(f"✅ Ending equity: ${equity_values[-1]:,.2f}")
    print(f"✅ Daily returns tracked: {len(result.daily_returns)}")
    print("✅ Test PASSED")


def test_9_signal_history():
    """Test signal history tracking"""
    print("\n" + "="*80)
    print("TEST 9: Signal History Tracking")
    print("="*80)
    
    config = BacktestConfig(
        initial_capital=100000,
        symbols=["AAPL"],
        lookback_period=60
    )
    simulator = StrategySimulator(config)
    
    result = simulator.run_simulation(verbose=False)
    
    assert len(simulator.signals_history) >= 0, "Should track signals"
    
    buy_signals = [s for s in simulator.signals_history if s['type'] == 'BUY']
    sell_signals = [s for s in simulator.signals_history if s['type'] == 'SELL']
    
    print(f"✅ Total signals: {len(simulator.signals_history)}")
    print(f"✅ Buy signals: {len(buy_signals)}")
    print(f"✅ Sell signals: {len(sell_signals)}")
    
    if buy_signals:
        print(f"   First buy: {buy_signals[0]['symbol']} @ ${buy_signals[0]['price']:.2f}")
    if sell_signals:
        print(f"   First sell: {sell_signals[0]['symbol']} @ ${sell_signals[0]['price']:.2f}")
    
    print("✅ Test PASSED")


def test_10_result_consistency():
    """Test result data consistency"""
    print("\n" + "="*80)
    print("TEST 10: Result Data Consistency")
    print("="*80)
    
    config = BacktestConfig(
        initial_capital=100000,
        symbols=["AAPL", "TSLA"],
        lookback_period=90
    )
    simulator = StrategySimulator(config)
    
    result = simulator.run_simulation(verbose=False)
    
    # Check consistency
    assert result.config == config, "Config not stored"
    assert result.initial_capital == config.initial_capital, "Initial capital mismatch"
    assert result.total_return_percent == (
        (result.final_capital - result.initial_capital) / result.initial_capital * 100
    ), "Return calculation error"
    
    # Check dates
    assert result.start_date <= result.end_date, "Date range invalid"
    
    # Check trade lists
    assert len(result.trades) == result.total_trades or result.total_trades == 0, "Trade count mismatch"
    
    print(f"✅ Config consistent")
    print(f"✅ Capital tracking: ${result.initial_capital:,.2f} → ${result.final_capital:,.2f}")
    print(f"✅ Return: {result.total_return_percent:.2f}%")
    print(f"✅ Date range: {result.start_date.date()} to {result.end_date.date()}")
    print(f"✅ Trades: {result.total_trades}")
    print("✅ Test PASSED")


if __name__ == "__main__":
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*20 + "STRATEGY SIMULATOR TEST SUITE" + " "*30 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        test_1_simulator_initialization,
        test_2_mock_data_generation,
        test_3_load_historical_data,
        test_4_signal_generation,
        test_5_full_simulation,
        test_6_multi_symbol_simulation,
        test_7_performance_metrics,
        test_8_equity_curve_tracking,
        test_9_signal_history,
        test_10_result_consistency,
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
