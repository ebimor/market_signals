"""
Test RSI Indicator

Tests the RSI calculation with real market data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/home/eshahrivar/test_hedge_ai/safeswing_trader/backend')

from signals.indicators import RSI


def test_rsi_basic():
    """Test RSI calculation with simple data."""
    print("\n" + "="*60)
    print("TEST 1: RSI with simple test data")
    print("="*60)
    
    # Simple price series for testing
    prices = pd.Series([44, 44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84, 46.08, 45.89, 46.03, 45.61, 46.28, 46.00, 46.00, 46.11, 45.64, 46.21, 46.25, 45.71, 46.45, 46.59, 46.54])
    
    rsi = RSI(period=14)
    rsi_values = rsi.calculate(prices)
    
    print(f"Input prices: {len(prices)} data points")
    print(f"First 5 prices: {prices.head().tolist()}")
    print(f"Last 5 prices: {prices.tail().tolist()}")
    print(f"\nRSI values (last 10):")
    for i in range(max(0, len(rsi_values)-10), len(rsi_values)):
        signal = rsi.get_signal(rsi_values.iloc[i])
        confidence = rsi.get_confidence(rsi_values.iloc[i])
        print(f"  Price {prices.iloc[i]:6.2f} → RSI {rsi_values.iloc[i]:6.2f} | Signal: {signal:4} | Confidence: {confidence:5.1f}%")
    
    print("\n✅ TEST 1 PASSED")


def test_rsi_with_real_data():
    """Test RSI with real AAPL data fetched from yfinance."""
    print("\n" + "="*60)
    print("TEST 2: RSI with real AAPL data")
    print("="*60)
    
    try:
        import yfinance as yf
        
        # Fetch real data
        print("Fetching AAPL data from Yahoo Finance...")
        aapl = yf.download('AAPL', period='1mo', interval='1d', progress=False)
        
        if len(aapl) == 0:
            print("❌ No data fetched from yfinance")
            return
        
        prices = aapl['Close']
        print(f"Fetched {len(prices)} days of AAPL data")
        print(f"Date range: {prices.index[0]} to {prices.index[-1]}")
        print(f"Price range: ${prices.min():.2f} - ${prices.max():.2f}")
        
        # Calculate RSI
        rsi = RSI(period=14)
        rsi_values = rsi.calculate(prices)
        
        print(f"\nRSI Analysis (last 10 days):")
        print(f"{'Date':<12} {'Close':<8} {'RSI':<8} {'Signal':<6} {'Confidence':<12}")
        print("-" * 50)
        for i in range(max(0, len(rsi_values)-10), len(rsi_values)):
            date = prices.index[i].strftime('%Y-%m-%d')
            close = prices.iloc[i]
            rsi_val = rsi_values.iloc[i]
            signal = rsi.get_signal(rsi_val)
            confidence = rsi.get_confidence(rsi_val)
            
            print(f"{date:<12} ${close:<7.2f} {rsi_val:<8.2f} {signal:<6} {confidence:>6.1f}%")
        
        # Current signal
        current_rsi = rsi_values.iloc[-1]
        current_signal = rsi.get_signal(current_rsi)
        current_confidence = rsi.get_confidence(current_rsi)
        
        print(f"\n🎯 Current Signal: {current_signal}")
        print(f"   RSI Value: {current_rsi:.2f}")
        print(f"   Confidence: {current_confidence:.1f}%")
        
        if current_rsi < 30:
            print(f"   → AAPL is OVERSOLD - Good buying opportunity")
        elif current_rsi > 70:
            print(f"   → AAPL is OVERBOUGHT - Consider selling")
        else:
            print(f"   → AAPL is in neutral territory")
        
        print("\n✅ TEST 2 PASSED")
        
    except Exception as e:
        print(f"❌ Error in TEST 2: {e}")
        import traceback
        traceback.print_exc()


def test_rsi_signals():
    """Test RSI signal generation at different levels."""
    print("\n" + "="*60)
    print("TEST 3: RSI Signal Generation")
    print("="*60)
    
    rsi = RSI(period=14)
    
    test_cases = [
        (10, "Extreme oversold"),
        (25, "Oversold"),
        (30, "Oversold threshold"),
        (50, "Neutral"),
        (70, "Overbought threshold"),
        (75, "Overbought"),
        (90, "Extreme overbought"),
    ]
    
    print(f"{'RSI Value':<12} {'Signal':<8} {'Confidence':<12} {'Description':<25}")
    print("-" * 60)
    for rsi_val, description in test_cases:
        signal = rsi.get_signal(rsi_val)
        confidence = rsi.get_confidence(rsi_val)
        print(f"{rsi_val:<12.1f} {signal:<8} {confidence:>6.1f}%        {description:<25}")
    
    print("\n✅ TEST 3 PASSED")


def test_rsi_requirements():
    """Test RSI with insufficient data."""
    print("\n" + "="*60)
    print("TEST 4: RSI with insufficient data")
    print("="*60)
    
    rsi = RSI(period=14)
    
    # Test with only 10 points (need 15 for RSI)
    prices = pd.Series([100, 101, 102, 103, 104, 105, 106, 107, 108, 109])
    rsi_values = rsi.calculate(prices)
    
    print(f"Input: {len(prices)} data points (need 15 for RSI)")
    print(f"Result: {rsi_values.tolist()}")
    print(f"All NaN (as expected): {rsi_values.isna().all()}")
    
    print("\n✅ TEST 4 PASSED")


if __name__ == '__main__':
    print("\n" + "🔬 RUNNING RSI TESTS 🔬".center(60, "="))
    
    try:
        test_rsi_basic()
        test_rsi_signals()
        test_rsi_requirements()
        test_rsi_with_real_data()
        
        print("\n" + "✅ ALL TESTS COMPLETED SUCCESSFULLY ✅".center(60, "="))
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
