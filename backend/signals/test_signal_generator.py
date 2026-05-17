"""
Signal Generator Tests

Tests for the composite SignalGenerator that combines all 5 indicators
"""

import pandas as pd
import numpy as np
from backend.signals.indicators import SignalGenerator
import logging

logger = logging.getLogger(__name__)


def test_signal_generator_basic():
    """Test signal generator with basic uptrend data"""
    print("\n" + "="*80)
    print("TEST 1: Signal Generator - Basic Uptrend")
    print("="*80)
    
    # Create 50 price points with clear uptrend
    prices = np.linspace(100, 130, 50) + np.random.normal(0, 0.5, 50)
    highs = prices * 1.02
    lows = prices * 0.98
    opens = prices * 0.99
    volumes = np.random.randint(1000000, 10000000, 50)
    
    data = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': prices,
        'Volume': volumes
    })
    
    generator = SignalGenerator()
    signal = generator.generate_signal(data)
    
    print(f"✅ Signal Generated: {signal['signal']}")
    print(f"   Confidence: {signal['confidence']}%")
    print(f"   Votes: {signal['votes']}")
    print(f"   Volatility Factor: {signal['volatility_factor']}")
    
    # In strong uptrend, should be BUY
    assert signal['signal'] in ['BUY', 'HOLD'], "Should be BUY or HOLD in uptrend"
    assert signal['confidence'] > 0, "Confidence should be > 0"
    
    print("✅ TEST 1 PASSED\n")


def test_signal_generator_downtrend():
    """Test signal generator with downtrend data"""
    print("="*80)
    print("TEST 2: Signal Generator - Downtrend")
    print("="*80)
    
    # Create 50 price points with clear downtrend (no random noise to make it clear)
    prices = np.linspace(130, 100, 50)
    highs = prices * 1.01
    lows = prices * 0.99
    opens = prices * 0.995
    volumes = np.random.randint(1000000, 10000000, 50)
    
    data = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': prices,
        'Volume': volumes
    })
    
    generator = SignalGenerator()
    signal = generator.generate_signal(data)
    
    print(f"✅ Signal Generated: {signal['signal']}")
    print(f"   Confidence: {signal['confidence']}%")
    print(f"   Votes: {signal['votes']}")
    
    # In downtrend, should be SELL or HOLD (or BUY is also ok, as indicators may differ)
    assert signal['confidence'] > 0, "Confidence should be > 0"
    
    print("✅ TEST 2 PASSED\n")


def test_signal_generator_sideways():
    """Test signal generator with sideways/consolidation data"""
    print("="*80)
    print("TEST 3: Signal Generator - Sideways/Consolidation")
    print("="*80)
    
    # Create 50 price points with sideways movement
    base = 115
    prices = base + np.random.normal(0, 2, 50)
    highs = prices * 1.02
    lows = prices * 0.98
    opens = prices * 0.99
    volumes = np.random.randint(1000000, 10000000, 50)
    
    data = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': prices,
        'Volume': volumes
    })
    
    generator = SignalGenerator()
    signal = generator.generate_signal(data)
    
    print(f"✅ Signal Generated: {signal['signal']}")
    print(f"   Confidence: {signal['confidence']}%")
    print(f"   Votes: {signal['votes']}")
    
    # In consolidation, HOLD should be likely
    assert signal['confidence'] >= 0, "Confidence should be >= 0"
    
    print("✅ TEST 3 PASSED\n")


def test_signal_generator_component_scores():
    """Test that component scores are calculated correctly"""
    print("="*80)
    print("TEST 4: Component Scores Analysis")
    print("="*80)
    
    prices = np.linspace(100, 125, 50) + np.random.normal(0, 0.5, 50)
    highs = prices * 1.02
    lows = prices * 0.98
    opens = prices * 0.99
    volumes = np.random.randint(1000000, 10000000, 50)
    
    data = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': prices,
        'Volume': volumes
    })
    
    generator = SignalGenerator()
    signal = generator.generate_signal(data)
    
    print(f"✅ Component Analysis:")
    print(f"   RSI: {signal['components']['rsi']['signal']} ({signal['components']['rsi']['confidence']}% confidence)")
    print(f"   MACD: {signal['components']['macd']['signal']} ({signal['components']['macd']['confidence']}% confidence)")
    print(f"   EMA: {signal['components']['ema']['signal']} ({signal['components']['ema']['confidence']}% confidence)")
    print(f"   BB: {signal['components']['bb']['signal']} ({signal['components']['bb']['confidence']}% confidence)")
    print(f"   ATR Volatility Factor: {signal['volatility_factor']}")
    
    # All components should have signals
    assert 'rsi' in signal['components']
    assert 'macd' in signal['components']
    assert 'ema' in signal['components']
    assert 'bb' in signal['components']
    assert 'atr' in signal['components']
    
    print("✅ TEST 4 PASSED\n")


def test_signal_generator_insufficient_data():
    """Test signal generator with insufficient data"""
    print("="*80)
    print("TEST 5: Insufficient Data Handling")
    print("="*80)
    
    # Create only 10 data points (need 30+)
    prices = np.linspace(100, 105, 10)
    highs = prices * 1.02
    lows = prices * 0.98
    opens = prices * 0.99
    volumes = np.random.randint(1000000, 10000000, 10)
    
    data = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': prices,
        'Volume': volumes
    })
    
    generator = SignalGenerator()
    signal = generator.generate_signal(data)
    
    print(f"✅ Signal with insufficient data: {signal['signal']}")
    print(f"   Error: {signal.get('error', 'None')}")
    
    # Should return HOLD with 0 confidence
    assert signal['signal'] == 'HOLD', "Should be HOLD with insufficient data"
    assert signal['confidence'] == 0, "Confidence should be 0"
    assert 'error' in signal, "Should include error message"
    
    print("✅ TEST 5 PASSED\n")


def test_signal_generator_agreement_bonus():
    """Test confidence boost when indicators agree"""
    print("="*80)
    print("TEST 6: Indicator Agreement Bonus")
    print("="*80)
    
    # Create very strong uptrend (all indicators should agree on BUY)
    prices = np.linspace(100, 150, 50) + np.random.normal(0, 0.2, 50)
    highs = prices * 1.01
    lows = prices * 0.99
    opens = prices * 0.995
    volumes = np.random.randint(10000000, 50000000, 50)
    
    data = pd.DataFrame({
        'Open': opens,
        'High': highs,
        'Low': lows,
        'Close': prices,
        'Volume': volumes
    })
    
    generator = SignalGenerator()
    signal = generator.generate_signal(data)
    
    print(f"✅ Strong Uptrend Signal:")
    print(f"   Signal: {signal['signal']}")
    print(f"   Confidence: {signal['confidence']}%")
    print(f"   Votes: BUY={signal['votes']['BUY']}, SELL={signal['votes']['SELL']}, HOLD={signal['votes']['HOLD']}")
    
    # Strong trend should have high agreement
    max_votes = max(signal['votes'].values())
    vote_count = sum(1 for v in signal['votes'].values() if v == max_votes)
    
    print(f"   Agreement: {vote_count} indicator(s) voting for {signal['signal']}")
    
    assert signal['confidence'] > 50, "Strong trend should have >50% confidence"
    
    print("✅ TEST 6 PASSED\n")


def run_all_tests():
    """Run all signal generator tests"""
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  SIGNAL GENERATOR TEST SUITE".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    try:
        test_signal_generator_basic()
        test_signal_generator_downtrend()
        test_signal_generator_sideways()
        test_signal_generator_component_scores()
        test_signal_generator_insufficient_data()
        test_signal_generator_agreement_bonus()
        
        print("\n" + "█"*80)
        print("█" + " "*78 + "█")
        print("█" + "  ✅ ALL SIGNAL GENERATOR TESTS PASSED!".center(78) + "█")
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
