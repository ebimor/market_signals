"""
Risk Engine Test Suite

Comprehensive tests for position sizing, stop-loss, take-profit, and portfolio allocation.
"""

import sys
sys.path.insert(0, '/home/eshahrivar/test_hedge_ai/safeswing_trader')

from backend.risk.risk_engine import RiskEngine, generate_sample_risk_analysis
import json


def test_position_sizing_basic():
    """Test basic position sizing calculation."""
    print("\n" + "="*80)
    print("TEST 1: Basic Position Sizing")
    print("="*80)
    
    engine = RiskEngine(account_balance=100000, risk_per_trade=0.02)
    
    # Test scenario: AAPL at $150, ATR = $3, confidence = 70%
    result = engine.calculate_position_size(
        entry_price=150,
        signal_confidence=70,
        atr=3,
        signal="BUY"
    )
    
    assert result["position_size"] > 0, "Position size should be > 0"
    assert result["position_value"] > 0, "Position value should be > 0"
    assert result["position_value"] <= engine.max_position_value, "Position should respect max size"
    
    print(f"✅ Position Size: {result['position_size']} shares")
    print(f"✅ Position Value: ${result['position_value']:,.2f}")
    print(f"✅ Risk Amount: ${result['risk_amount']:,.2f} ({result['risk_percentage']:.2f}% of account)")
    print(f"✅ Test PASSED")
    return True


def test_position_sizing_confidence_impact():
    """Test that confidence affects position sizing."""
    print("\n" + "="*80)
    print("TEST 2: Confidence Impact on Position Sizing")
    print("="*80)
    
    engine = RiskEngine(account_balance=100000, risk_per_trade=0.02)
    
    # Low confidence
    low_conf = engine.calculate_position_size(150, 30, 3, "BUY")
    
    # High confidence
    high_conf = engine.calculate_position_size(150, 90, 3, "BUY")
    
    print(f"✅ Low Confidence (30%): {low_conf['position_size']} shares")
    print(f"✅ High Confidence (90%): {high_conf['position_size']} shares")
    
    assert high_conf["position_size"] > low_conf["position_size"], \
        "Higher confidence should result in larger position"
    
    print(f"✅ Multiplier difference: {high_conf['position_size']/low_conf['position_size']:.2f}x")
    print(f"✅ Test PASSED")
    return True


def test_exits_buy_signal():
    """Test stop-loss and take-profit calculation for BUY."""
    print("\n" + "="*80)
    print("TEST 3: Exit Levels - BUY Signal")
    print("="*80)
    
    engine = RiskEngine(
        account_balance=100000,
        sl_atr_multiple=2.0,
        tp_atr_multiple=3.0,
        min_reward_ratio=2.0
    )
    
    exits = engine.calculate_exits(
        entry_price=100,
        atr=2,  # $2 ATR
        signal="BUY"
    )
    
    # Expected: SL = 100 - (2*2) = 96, TP = 100 + (3*2) = 106
    assert exits["stop_loss"] == 96, f"SL should be 96, got {exits['stop_loss']}"
    assert exits["take_profit"] == 106, f"TP should be 106, got {exits['take_profit']}"
    assert exits["risk_per_share"] == 4, f"Risk per share should be 4, got {exits['risk_per_share']}"
    assert exits["reward_per_share"] == 6, f"Reward per share should be 6, got {exits['reward_per_share']}"
    assert exits["risk_reward_ratio"] == 1.5, f"R/R ratio should be 1.5, got {exits['risk_reward_ratio']}"
    
    print(f"✅ Entry: ${exits['entry_price']}")
    print(f"✅ Stop Loss: ${exits['stop_loss']} (risk: ${exits['risk_per_share']}/share)")
    print(f"✅ Take Profit: ${exits['take_profit']} (reward: ${exits['reward_per_share']}/share)")
    print(f"✅ Risk/Reward Ratio: 1:{exits['risk_reward_ratio']}")
    print(f"✅ Test PASSED")
    return True


def test_exits_sell_signal():
    """Test stop-loss and take-profit calculation for SELL."""
    print("\n" + "="*80)
    print("TEST 4: Exit Levels - SELL Signal")
    print("="*80)
    
    engine = RiskEngine(
        account_balance=100000,
        sl_atr_multiple=2.0,
        tp_atr_multiple=3.0,
        min_reward_ratio=2.0
    )
    
    exits = engine.calculate_exits(
        entry_price=100,
        atr=2,  # $2 ATR
        signal="SELL"
    )
    
    # Expected: SL = 100 + (2*2) = 104, TP = 100 - (3*2) = 94
    assert exits["stop_loss"] == 104, f"SL should be 104, got {exits['stop_loss']}"
    assert exits["take_profit"] == 94, f"TP should be 94, got {exits['take_profit']}"
    assert exits["risk_per_share"] == 4, f"Risk per share should be 4"
    assert exits["reward_per_share"] == 6, f"Reward per share should be 6"
    
    print(f"✅ Entry: ${exits['entry_price']}")
    print(f"✅ Stop Loss: ${exits['stop_loss']} (SELL SL above entry)")
    print(f"✅ Take Profit: ${exits['take_profit']} (SELL TP below entry)")
    print(f"✅ Risk/Reward Ratio: 1:{exits['risk_reward_ratio']}")
    print(f"✅ Test PASSED")
    return True


def test_full_trade_plan():
    """Test complete trade plan generation."""
    print("\n" + "="*80)
    print("TEST 5: Full Trade Plan Generation")
    print("="*80)
    
    engine = RiskEngine(account_balance=100000, risk_per_trade=0.02)
    
    trade_plan = engine.calculate_full_trade_plan(
        entry_price=150,
        signal_confidence=75,
        atr=3,
        signal="BUY",
        ticker="AAPL"
    )
    
    assert trade_plan["position"]["size"] > 0, "Position size should be > 0"
    assert trade_plan["exits"]["risk_reward_ratio"] > 0, "R/R ratio should be > 0"
    assert "potential_loss" in trade_plan["metrics"], "Should have potential loss"
    assert "potential_gain" in trade_plan["metrics"], "Should have potential gain"
    assert "expected_value" in trade_plan["metrics"], "Should have expected value"
    
    print(f"✅ Ticker: {trade_plan['ticker']}")
    print(f"✅ Signal: {trade_plan['signal']} @ ${trade_plan['entry_price']} (Confidence: {trade_plan['confidence']:.1f}%)")
    print(f"✅ Position: {trade_plan['position']['size']} shares (${trade_plan['position']['value']:,.2f})")
    print(f"✅ SL: ${trade_plan['exits']['stop_loss']} | TP: ${trade_plan['exits']['take_profit']}")
    print(f"✅ Max Loss: ${trade_plan['metrics']['potential_loss']:,.2f}")
    print(f"✅ Max Gain: ${trade_plan['metrics']['potential_gain']:,.2f}")
    print(f"✅ Expected Value: ${trade_plan['metrics']['expected_value']:,.2f}")
    print(f"✅ Valid: {trade_plan['valid']}")
    print(f"✅ Test PASSED")
    return True


def test_portfolio_allocation():
    """Test portfolio allocation calculation."""
    print("\n" + "="*80)
    print("TEST 6: Portfolio Allocation")
    print("="*80)
    
    engine = RiskEngine(account_balance=100000, max_open_positions=5)
    
    # Scenario 1: No open positions
    alloc_empty = engine.calculate_portfolio_allocation(open_positions=0, new_signal_confidence=80)
    assert alloc_empty["can_open_new_position"] == True, "Should be able to open when no positions"
    assert alloc_empty["slots_available"] == 5, "Should have 5 slots available"
    
    print(f"✅ Scenario 1 (0/5 positions):")
    print(f"   - Can open new: {alloc_empty['can_open_new_position']}")
    print(f"   - Slots available: {alloc_empty['slots_available']}")
    print(f"   - Recommended risk: ${alloc_empty['recommended_risk_amount']:,.2f}")
    
    # Scenario 2: Full allocation
    alloc_full = engine.calculate_portfolio_allocation(open_positions=5, new_signal_confidence=80)
    assert alloc_full["can_open_new_position"] == False, "Should not open when at max"
    assert alloc_full["slots_available"] == 0, "Should have 0 slots available"
    
    print(f"✅ Scenario 2 (5/5 positions):")
    print(f"   - Can open new: {alloc_full['can_open_new_position']}")
    print(f"   - Slots available: {alloc_full['slots_available']}")
    print(f"   - Remaining cash: ${alloc_full['remaining_cash']:,.2f}")
    
    # Scenario 3: Partial allocation
    alloc_partial = engine.calculate_portfolio_allocation(open_positions=2, new_signal_confidence=90)
    assert alloc_partial["can_open_new_position"] == True, "Should be able to open"
    assert alloc_partial["slots_available"] == 3, "Should have 3 slots"
    
    print(f"✅ Scenario 3 (2/5 positions, 90% confidence):")
    print(f"   - Can open new: {alloc_partial['can_open_new_position']}")
    print(f"   - Slots available: {alloc_partial['slots_available']}")
    print(f"   - Recommended risk: ${alloc_partial['recommended_risk_amount']:,.2f}")
    
    print(f"✅ Test PASSED")
    return True


def test_max_drawdown_limits():
    """Test maximum drawdown limits."""
    print("\n" + "="*80)
    print("TEST 7: Max Drawdown Limits")
    print("="*80)
    
    engine = RiskEngine(account_balance=100000)
    limits = engine.get_max_drawdown_limit()
    
    print(f"✅ Daily Loss Limit: ${limits['daily_loss_limit']:,.2f} (2% of account)")
    print(f"✅ Weekly Loss Limit: ${limits['weekly_loss_limit']:,.2f} (5% of account)")
    print(f"✅ Monthly Loss Limit: ${limits['monthly_loss_limit']:,.2f} (10% of account)")
    print(f"✅ Account Stop Loss: ${limits['account_stop_loss']:,.2f} (20% of account)")
    
    assert limits["daily_loss_limit"] == 2000
    assert limits["weekly_loss_limit"] == 5000
    assert limits["monthly_loss_limit"] == 10000
    assert limits["account_stop_loss"] == 20000
    
    print(f"✅ Test PASSED")
    return True


def test_trade_validation():
    """Test trade plan validation."""
    print("\n" + "="*80)
    print("TEST 8: Trade Validation")
    print("="*80)
    
    engine = RiskEngine(account_balance=100000, min_reward_ratio=2.0)
    
    # Valid trade
    valid_plan = engine.calculate_full_trade_plan(150, 80, 3, "BUY", "AAPL")
    is_valid, warnings = engine.validate_trade(valid_plan)
    
    print(f"✅ Valid Trade:")
    print(f"   - Valid: {is_valid}")
    print(f"   - Warnings: {warnings if warnings else 'None'}")
    
    # Test with sample analysis function
    analysis = generate_sample_risk_analysis(
        ticker="TSLA",
        price=250,
        atr=4,
        confidence=65,
        signal="BUY",
        account_balance=100000
    )
    
    print(f"\n✅ Sample Analysis - TSLA:")
    print(f"   - Valid: {analysis['validation']['is_valid']}")
    print(f"   - Warnings: {analysis['validation']['warnings'] if analysis['validation']['warnings'] else 'None'}")
    print(f"   - Position: {analysis['trade_plan']['position']['size']} shares")
    print(f"   - Max Loss: ${analysis['trade_plan']['metrics']['potential_loss']:,.2f}")
    
    print(f"\n✅ Test PASSED")
    return True


def test_risk_engine_different_accounts():
    """Test risk engine with different account sizes."""
    print("\n" + "="*80)
    print("TEST 9: Risk Engine with Different Account Sizes")
    print("="*80)
    
    # Small account: $10,000
    engine_small = RiskEngine(account_balance=10000, risk_per_trade=0.02)
    pos_small = engine_small.calculate_position_size(100, 75, 2, "BUY")
    
    print(f"✅ $10,000 Account:")
    print(f"   - Risk per trade: ${engine_small.risk_amount:,.2f}")
    print(f"   - Position size: {pos_small['position_size']} shares")
    print(f"   - Position value: ${pos_small['position_value']:,.2f}")
    
    # Large account: $1,000,000
    engine_large = RiskEngine(account_balance=1000000, risk_per_trade=0.02)
    pos_large = engine_large.calculate_position_size(100, 75, 2, "BUY")
    
    print(f"✅ $1,000,000 Account:")
    print(f"   - Risk per trade: ${engine_large.risk_amount:,.2f}")
    print(f"   - Position size: {pos_large['position_size']} shares")
    print(f"   - Position value: ${pos_large['position_value']:,.2f}")
    
    # Verify scaling
    assert pos_large["position_size"] > pos_small["position_size"], \
        "Larger account should have larger positions"
    
    print(f"✅ Position size ratio: {pos_large['position_size']/pos_small['position_size']:.1f}x")
    print(f"✅ Test PASSED")
    return True


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "="*80)
    print("TEST 10: Edge Cases and Error Handling")
    print("="*80)
    
    engine = RiskEngine(account_balance=100000)
    
    # Zero price
    result1 = engine.calculate_position_size(0, 50, 2, "BUY")
    assert result1["position_size"] == 0, "Should handle zero price"
    print(f"✅ Zero price handled: {result1['position_size']} shares")
    
    # Zero ATR
    result2 = engine.calculate_position_size(100, 50, 0, "BUY")
    assert result2["position_size"] == 0, "Should handle zero ATR"
    print(f"✅ Zero ATR handled: {result2['position_size']} shares")
    
    # Extreme confidence (0%)
    result3 = engine.calculate_position_size(100, 0, 2, "BUY")
    assert result3["position_size"] >= 0, "Should handle 0% confidence"
    print(f"✅ 0% confidence handled: {result3['position_size']} shares")
    
    # Extreme confidence (100%)
    result4 = engine.calculate_position_size(100, 100, 2, "BUY")
    assert result4["position_size"] > 0, "Should handle 100% confidence"
    print(f"✅ 100% confidence handled: {result4['position_size']} shares")
    
    # Very small ATR (high volatility protection)
    result5 = engine.calculate_position_size(100, 75, 0.1, "BUY")
    assert result5["position_size"] > 0, "Should handle tiny ATR"
    print(f"✅ Tiny ATR (0.1) handled: {result5['position_size']} shares")
    
    # Very large ATR (large spread)
    result6 = engine.calculate_position_size(100, 75, 50, "BUY")
    assert result6["position_size"] >= 0, "Should handle large ATR"
    print(f"✅ Large ATR (50) handled: {result6['position_size']} shares")
    
    print(f"\n✅ Test PASSED")
    return True


def run_all_tests():
    """Run all test cases."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "RISK ENGINE TEST SUITE".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        test_position_sizing_basic,
        test_position_sizing_confidence_impact,
        test_exits_buy_signal,
        test_exits_sell_signal,
        test_full_trade_plan,
        test_portfolio_allocation,
        test_max_drawdown_limits,
        test_trade_validation,
        test_risk_engine_different_accounts,
        test_edge_cases,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except AssertionError as e:
            failed += 1
            print(f"\n❌ FAILED: {str(e)}")
        except Exception as e:
            failed += 1
            print(f"\n❌ ERROR: {str(e)}")
    
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print(f"║ TESTS PASSED: {passed}/10".ljust(79) + "║")
    print(f"║ TESTS FAILED: {failed}/10".ljust(79) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
