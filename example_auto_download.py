#!/usr/bin/env python3
"""
Complete example: Download data automatically and run backtests

This script demonstrates the full workflow:
1. Auto-download data from yfinance (with caching)
2. Load data into simulator
3. Run backtest
4. Display results
"""

from backend.backtesting.strategy_simulator import StrategySimulator, BacktestConfig
from backend.data.data_loader import DataLoader
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

print()
print("="*70)
print("SafeSwing Trader - Automated Backtest with Data Download")
print("="*70)
print()

# ============================================================================
# EXAMPLE 1: Single Symbol Backtest
# ============================================================================
print("EXAMPLE 1: Single Symbol Backtest")
print("-" * 70)

config = BacktestConfig(
    initial_capital=100000,
    symbols=["TSLA"],
    lookback_period=60
)

simulator = StrategySimulator(config)

# Auto-download TSLA (cached for future runs)
print("Downloading TSLA data (1 year)...")
simulator.download_data("TSLA", period="1y")

# Run backtest
print("Running backtest...")
result = simulator.run_simulation(verbose=False)

print()
print("RESULTS:")
print(f"  Capital:      ${result.initial_capital:,.0f} → ${result.final_capital:,.0f}")
print(f"  Return:       {result.total_return_percent:+.2f}%")
print(f"  Total Trades: {result.total_trades}")
if result.total_trades > 0:
    print(f"  Win Rate:     {result.win_rate_percent:.1f}%")
    print(f"  Profit Factor: {result.profit_factor:.2f}")
    print(f"  Avg Winner:   ${result.avg_winner:,.2f}")
    print(f"  Avg Loser:    ${result.avg_loser:,.2f}")
print(f"  Max Drawdown: {result.max_drawdown_percent:.2f}%")
print()

# ============================================================================
# EXAMPLE 2: Multi-Symbol Portfolio Backtest
# ============================================================================
print("EXAMPLE 2: Multi-Symbol Portfolio Backtest")
print("-" * 70)

config = BacktestConfig(
    initial_capital=250000,
    symbols=["AAPL", "MSFT", "TSLA", "GOOGL"],
    max_portfolio_exposure=0.50,
    max_position_size=0.15,
    lookback_period=60
)

simulator = StrategySimulator(config)

# Auto-download multiple symbols (cached for future runs)
print("Downloading data for 4 symbols (6 months)...")
try:
    simulator.download_multiple(["AAPL", "MSFT", "TSLA", "GOOGL"], period="6mo")
    print(f"Loaded {len(simulator.price_data)} symbols")
    
    # Run backtest
    print("Running portfolio backtest...")
    result = simulator.run_simulation(verbose=False)
    
    print()
    print("PORTFOLIO RESULTS:")
    print(f"  Capital:      ${result.initial_capital:,.0f} → ${result.final_capital:,.0f}")
    print(f"  Return:       {result.total_return_percent:+.2f}%")
    print(f"  Total Trades: {result.total_trades}")
    if result.total_trades > 0:
        print(f"  Win Rate:     {result.win_rate_percent:.1f}%")
        print(f"  Profit Factor: {result.profit_factor:.2f}")
    print(f"  Max Drawdown: {result.max_drawdown_percent:.2f}%")
except Exception as e:
    print(f"Note: Multi-symbol download may fail due to yfinance API availability")
    print(f"Error: {e}")

print()

# ============================================================================
# EXAMPLE 3: Check Cached Data
# ============================================================================
print("EXAMPLE 3: Check Cached Data")
print("-" * 70)

cached = DataLoader.get_cached_symbols()
print(f"Cached symbols: {cached}")
print()

for symbol in cached:
    info = DataLoader.get_cache_info(symbol)
    if info:
        print(f"{symbol}:")
        print(f"  Rows:        {info['rows']}")
        print(f"  Date range:  {info['start_date']} to {info['end_date']}")
        print(f"  File size:   {info['file_size_kb']:.1f} KB")

print()

# ============================================================================
# NOTES
# ============================================================================
print("="*70)
print("NOTES:")
print("="*70)
print()
print("✅ Data is automatically downloaded from yfinance")
print("✅ Downloaded data is cached in backend/data/cache/")
print("✅ Subsequent runs load from cache (instant, no re-download)")
print("✅ Use force_refresh=True to re-download data")
print()
print("Cache management:")
print("  DataLoader.clear_cache('TSLA')  # Clear specific symbol")
print("  DataLoader.clear_cache()        # Clear all cache")
print()

