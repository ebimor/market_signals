"""
MACD Indicator Tests

Tests for MACD (Moving Average Convergence Divergence) indicator
"""

import pandas as pd
import numpy as np
from backend.signals.indicators import MACD
import logging

logger = logging.getLogger(__name__)


def test_macd_basic_calculation():
    """Test MACD calculation with synthetic data"""
    print("\n" + "="*80)
    print("TEST 1: Basic MACD Calculation")
    print("="*80)
    
    # Create 100 price points with uptrend
    prices = pd.Series(np.linspace(100, 150, 100) + np.random.normal(0, 1, 100))
    
    # Calculate MACD
    macd = MACD(fast=12, slow=26, signal=9)
    macd_line, signal_line, histogram = macd.calculate(prices)
    
    print(f"✅ MACD calculated successfully")
    print(f"   Data points: {len(prices)}")
    print(f"   MACD line (last 5): {macd_line.iloc[-5:].round(4).tolist()}")
    print(f"   Signal line (last 5): {signal_line.iloc[-5:].round(4).tolist()}")
    print(f"   Histogram (last 5): {histogram.iloc[-5:].round(4).tolist()}")
    
    # Verify structure
    assert len(macd_line) == len(prices), "MACD line length mismatch"
    assert len(signal_line) == len(prices), "Signal line length mismatch"
    assert len(histogram) == len(prices), "Histogram length mismatch"
    
    # Check that final values are not NaN
    assert not pd.isna(macd_line.iloc[-1]), "Final MACD value should not be NaN"
    assert not pd.isna(signal_line.iloc[-1]), "Final signal value should not be NaN"
    assert not pd.isna(histogram.iloc[-1]), "Final histogram value should not be NaN"
    
    print("✅ TEST 1 PASSED\n")


def test_macd_with_real_pattern():
    """Test MACD with a realistic price pattern"""
    print("="*80)
    print("TEST 2: MACD with Real Price Pattern")
    print("="*80)
    
    # Create prices with clear trend
    prices = pd.Series([
        100.0, 101.5, 102.3, 101.8, 103.2, 104.1, 105.3, 106.2, 107.5, 108.3,
        109.1, 110.2, 111.5, 112.3, 113.1, 114.2, 115.3, 116.1, 117.2, 118.5,
        119.3, 120.1, 121.2, 122.3, 123.1, 124.2, 125.3, 126.1, 127.5, 128.3,
        129.2, 130.5, 131.3, 132.1, 133.2, 134.3, 135.1, 136.2, 137.5, 138.3,
        # Peak and slight reversal
        139.5, 139.2, 138.8, 138.3, 137.9, 137.5, 137.2, 136.8, 136.3, 135.9,
    ])
    
    macd = MACD(fast=12, slow=26, signal=9)
    macd_line, signal_line, histogram = macd.calculate(prices)
    
    current_macd = macd_line.iloc[-1]
    current_signal = signal_line.iloc[-1]
    current_histogram = histogram.iloc[-1]
    
    print(f"✅ MACD values at end:")
    print(f"   MACD: {current_macd:.4f}")
    print(f"   Signal: {current_signal:.4f}")
    print(f"   Histogram: {current_histogram:.4f}")
    
    # Verify logic: in an uptrend, MACD line should be positive
    assert current_macd > 0, "MACD should be positive in strong uptrend"
    
    print("✅ TEST 2 PASSED\n")


def test_macd_signal_generation():
    """Test MACD signal generation logic"""
    print("="*80)
    print("TEST 3: MACD Signal Generation")
    print("="*80)
    
    # Uptrend - MACD should be positive and above signal
    uptrend_prices = pd.Series(np.linspace(100, 120, 50) + np.random.normal(0, 0.5, 50))
    
    macd = MACD()
    macd_line_up, signal_line_up, histogram_up = macd.calculate(uptrend_prices)
    
    print(f"✅ Uptrend Analysis:")
    print(f"   MACD: {macd_line_up.iloc[-1]:.4f}")
    print(f"   Signal: {signal_line_up.iloc[-1]:.4f}")
    print(f"   Histogram: {histogram_up.iloc[-1]:.4f}")
    
    # In uptrend: histogram should be positive
    assert histogram_up.iloc[-1] > 0, "Histogram should be positive in uptrend"
    
    # Downtrend - MACD should be negative and below signal
    downtrend_prices = pd.Series(np.linspace(120, 100, 50) + np.random.normal(0, 0.5, 50))
    macd_line_down, signal_line_down, histogram_down = macd.calculate(downtrend_prices)
    
    print(f"\n✅ Downtrend Analysis:")
    print(f"   MACD: {macd_line_down.iloc[-1]:.4f}")
    print(f"   Signal: {signal_line_down.iloc[-1]:.4f}")
    print(f"   Histogram: {histogram_down.iloc[-1]:.4f}")
    
    # In downtrend: histogram should be negative
    assert histogram_down.iloc[-1] < 0, "Histogram should be negative in downtrend"
    
    print("✅ TEST 3 PASSED\n")


def test_macd_different_parameters():
    """Test MACD with different parameter combinations"""
    print("="*80)
    print("TEST 4: MACD with Different Parameters")
    print("="*80)
    
    prices = pd.Series(np.linspace(100, 150, 100) + np.random.normal(0, 1, 100))
    
    # Standard parameters
    macd_std = MACD(fast=12, slow=26, signal=9)
    macd_line_std, signal_line_std, _ = macd_std.calculate(prices)
    
    # Fast parameters (more responsive)
    macd_fast = MACD(fast=5, slow=13, signal=5)
    macd_line_fast, signal_line_fast, _ = macd_fast.calculate(prices)
    
    # Slow parameters (less responsive)
    macd_slow = MACD(fast=20, slow=40, signal=12)
    macd_line_slow, signal_line_slow, _ = macd_slow.calculate(prices)
    
    print(f"✅ Standard (12, 26, 9):")
    print(f"   MACD: {macd_line_std.iloc[-1]:.4f}")
    print(f"   Signal: {signal_line_std.iloc[-1]:.4f}")
    
    print(f"\n✅ Fast (5, 13, 5):")
    print(f"   MACD: {macd_line_fast.iloc[-1]:.4f}")
    print(f"   Signal: {signal_line_fast.iloc[-1]:.4f}")
    
    print(f"\n✅ Slow (20, 40, 12):")
    print(f"   MACD: {macd_line_slow.iloc[-1]:.4f}")
    print(f"   Signal: {signal_line_slow.iloc[-1]:.4f}")
    
    print("✅ TEST 4 PASSED\n")


def test_macd_insufficient_data():
    """Test MACD with insufficient data"""
    print("="*80)
    print("TEST 5: MACD with Insufficient Data")
    print("="*80)
    
    # Only 10 prices (less than slow period of 26)
    prices = pd.Series(np.linspace(100, 110, 10))
    
    macd = MACD(fast=12, slow=26, signal=9)
    macd_line, signal_line, histogram = macd.calculate(prices)
    
    print(f"✅ Data points: {len(prices)} (less than slow period 26)")
    print(f"   All values should be NaN initially")
    print(f"   MACD values: {macd_line.tolist()}")
    
    # Should return all NaN
    assert macd_line.isna().all(), "MACD should be all NaN with insufficient data"
    
    print("✅ TEST 5 PASSED\n")


def run_all_tests():
    """Run all MACD tests"""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  MACD (Moving Average Convergence Divergence) TEST SUITE".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    try:
        test_macd_basic_calculation()
        test_macd_with_real_pattern()
        test_macd_signal_generation()
        test_macd_different_parameters()
        test_macd_insufficient_data()
        
        print("\n" + "█"*80)
        print("█" + " "*78 + "█")
        print("█" + "  ✅ ALL MACD TESTS PASSED!".center(78) + "█")
        print("█" + " "*78 + "█")
        print("█"*80 + "\n")
        
        return True
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = run_all_tests()
    exit(0 if success else 1)
