"""
Portfolio Exposure Tests

Tests for maximum portfolio exposure limits and position sizing adjustments.
"""

import sys
sys.path.insert(0, '/home/eshahrivar/test_hedge_ai/safeswing_trader')

from backend.risk.risk_engine import RiskEngine


def test_portfolio_exposure_calculation():
    """Test basic portfolio exposure calculation."""
    print("\n" + "="*80)
    print("TEST 1: Portfolio Exposure Calculation")
    print("="*80)
    
    engine = RiskEngine(
        account_balance=100000,
        max_portfolio_exposure=0.50  # 50% max
    )
    
    # No positions
    exposure1 = engine.calculate_portfolio_exposure([])
    assert exposure1['current_exposure']['total_position_value'] == 0
    assert exposure1['remaining_capacity']['available_position_value'] == 50000
    assert exposure1['constraints']['can_add_position'] == True
    
    print(f"✅ No positions: ${exposure1['remaining_capacity']['available_position_value']:,.2f} available")
    
    # With 2 positions ($15k each = $30k total)
    positions = [
        {'value': 15000, 'risk': 300},
        {'value': 15000, 'risk': 300}
    ]
    exposure2 = engine.calculate_portfolio_exposure(positions)
    assert exposure2['current_exposure']['total_position_value'] == 30000
    assert exposure2['remaining_capacity']['available_position_value'] == 20000
    assert exposure2['constraints']['can_add_position'] == True
    
    print(f"✅ 2 positions ($30k): ${exposure2['remaining_capacity']['available_position_value']:,.2f} remaining")
    
    # At limit ($50k)
    positions_full = [
        {'value': 25000, 'risk': 500},
        {'value': 25000, 'risk': 500}
    ]
    exposure3 = engine.calculate_portfolio_exposure(positions_full)
    assert exposure3['current_exposure']['total_position_value'] == 50000
    assert exposure3['constraints']['at_exposure_limit'] == True
    assert exposure3['constraints']['can_add_position'] == False
    
    print(f"✅ At limit ($50k): can_add_position = {exposure3['constraints']['can_add_position']}")
    print(f"✅ Test PASSED")
    return True


def test_position_size_adjustment_no_adjustment_needed():
    """Test position size adjustment when within limits."""
    print("\n" + "="*80)
    print("TEST 2: Position Size - No Adjustment Needed")
    print("="*80)
    
    engine = RiskEngine(
        account_balance=100000,
        max_portfolio_exposure=0.50
    )
    
    # Propose $10k position with $30k already deployed
    open_positions = [{'value': 30000, 'risk': 600}]
    adjustment = engine.adjust_position_size_for_exposure(
        position_size=100,
        entry_price=100,
        open_positions=open_positions
    )
    
    assert adjustment['was_adjusted'] == False
    assert adjustment['adjusted_position_size'] == 100
    assert adjustment['reduction_percentage'] == 0
    
    print(f"✅ Proposed: 100 shares @ $100 = $10,000")
    print(f"✅ Available: $20,000 capacity")
    print(f"✅ Adjusted: No (fits within limits)")
    print(f"✅ Test PASSED")
    return True


def test_position_size_adjustment_partial():
    """Test position size adjustment when partially at limit."""
    print("\n" + "="*80)
    print("TEST 3: Position Size - Partial Adjustment")
    print("="*80)
    
    engine = RiskEngine(
        account_balance=100000,
        max_portfolio_exposure=0.50
    )
    
    # Propose $15k position with $40k already deployed (only $10k capacity left)
    open_positions = [{'value': 40000, 'risk': 800}]
    adjustment = engine.adjust_position_size_for_exposure(
        position_size=150,
        entry_price=100,
        open_positions=open_positions
    )
    
    assert adjustment['was_adjusted'] == True
    assert adjustment['original_position_size'] == 150
    assert adjustment['adjusted_position_size'] == 100  # 100 shares * $100 = $10k (fits)
    assert adjustment['reduction_percentage'] > 0
    
    print(f"✅ Proposed: 150 shares @ $100 = $15,000")
    print(f"✅ Available: $10,000 capacity")
    print(f"✅ Adjusted: 100 shares @ $100 = $10,000")
    print(f"✅ Reduction: {adjustment['reduction_percentage']:.1f}%")
    print(f"✅ Test PASSED")
    return True


def test_position_size_adjustment_full_block():
    """Test position size adjustment when at limit."""
    print("\n" + "="*80)
    print("TEST 4: Position Size - Full Block (At Limit)")
    print("="*80)
    
    engine = RiskEngine(
        account_balance=100000,
        max_portfolio_exposure=0.50
    )
    
    # Try to add position when already at $50k limit
    open_positions = [
        {'value': 25000, 'risk': 500},
        {'value': 25000, 'risk': 500}
    ]
    adjustment = engine.adjust_position_size_for_exposure(
        position_size=100,
        entry_price=100,
        open_positions=open_positions
    )
    
    assert adjustment['was_adjusted'] == True
    assert adjustment['adjusted_position_size'] == 0
    assert adjustment['reduction_percentage'] == 100
    
    print(f"✅ Proposed: 100 shares @ $100 = $10,000")
    print(f"✅ Available: $0 capacity (at limit)")
    print(f"✅ Adjusted: 0 shares (blocked)")
    print(f"✅ Reduction: {adjustment['reduction_percentage']:.1f}%")
    print(f"✅ Test PASSED")
    return True


def test_position_sizing_with_exposure():
    """Test full position sizing with exposure constraints."""
    print("\n" + "="*80)
    print("TEST 5: Full Position Sizing - With Exposure Constraints")
    print("="*80)
    
    engine = RiskEngine(
        account_balance=100000,
        max_portfolio_exposure=0.50,
        risk_per_trade=0.02
    )
    
    # Position sizing with partial exposure (stays within limits, no adjustment needed)
    open_positions = [{'value': 35000, 'risk': 700}]
    position = engine.calculate_position_size(
        entry_price=150,
        signal_confidence=75,
        atr=3,
        signal="BUY",
        open_positions=open_positions
    )
    
    assert position['position_size'] > 0
    assert position['portfolio_exposure']['remaining_capacity']['available_position_value'] == 15000
    
    print(f"✅ Entry: $150, Confidence: 75%, ATR: $3")
    print(f"✅ Position: {position['position_size']} shares (${position['position_value']:,.2f})")
    print(f"✅ Available: $15,000 capacity")
    print(f"✅ Was Adjusted: {position['exposure_adjustment']['was_adjusted']}")
    print(f"✅ Reason: {position['exposure_adjustment']['reduction_reason']}")
    print(f"✅ Test PASSED")
    return True


def test_portfolio_exposure_different_limits():
    """Test portfolio exposure with different exposure limits."""
    print("\n" + "="*80)
    print("TEST 6: Portfolio Exposure - Different Limits")
    print("="*80)
    
    # Conservative: 30% max exposure
    engine_conservative = RiskEngine(
        account_balance=100000,
        max_portfolio_exposure=0.30
    )
    
    exposure_cons = engine_conservative.calculate_portfolio_exposure([])
    assert exposure_cons['limits']['max_portfolio_value'] == 30000
    
    print(f"✅ Conservative (30%): Max ${exposure_cons['limits']['max_portfolio_value']:,.2f}")
    
    # Aggressive: 75% max exposure
    engine_aggressive = RiskEngine(
        account_balance=100000,
        max_portfolio_exposure=0.75
    )
    
    exposure_agg = engine_aggressive.calculate_portfolio_exposure([])
    assert exposure_agg['limits']['max_portfolio_value'] == 75000
    
    print(f"✅ Aggressive (75%): Max ${exposure_agg['limits']['max_portfolio_value']:,.2f}")
    print(f"✅ Test PASSED")
    return True


def test_full_trade_plan_with_exposure():
    """Test complete trade plan generation with exposure constraints."""
    print("\n" + "="*80)
    print("TEST 7: Full Trade Plan - With Exposure Constraints")
    print("="*80)
    
    engine = RiskEngine(
        account_balance=100000,
        max_portfolio_exposure=0.50
    )
    
    # Trade plan with exposure consideration
    open_positions = [{'value': 20000, 'risk': 400}]
    trade_plan = engine.calculate_full_trade_plan(
        entry_price=150,
        signal_confidence=80,
        atr=3,
        signal="BUY",
        ticker="AAPL",
        open_positions=open_positions
    )
    
    assert 'portfolio_exposure' in trade_plan
    assert 'exposure_adjustment' in trade_plan
    assert trade_plan['position']['size'] > 0
    
    print(f"✅ Ticker: {trade_plan['ticker']}")
    print(f"✅ Signal: {trade_plan['signal']} @ ${trade_plan['entry_price']}")
    print(f"✅ Position: {trade_plan['position']['size']} shares")
    print(f"✅ Exposure: {trade_plan['portfolio_exposure']['current_exposure']['exposure_percentage']:.1f}%")
    print(f"✅ Adjustment: {trade_plan['exposure_adjustment']['was_adjusted']}")
    print(f"✅ Test PASSED")
    return True


def test_exposure_with_account_scaling():
    """Test portfolio exposure scales correctly with account size."""
    print("\n" + "="*80)
    print("TEST 8: Exposure Scaling - Different Account Sizes")
    print("="*80)
    
    # Small account
    engine_small = RiskEngine(account_balance=10000, max_portfolio_exposure=0.50)
    exposure_small = engine_small.calculate_portfolio_exposure([])
    assert exposure_small['limits']['max_portfolio_value'] == 5000
    
    print(f"✅ $10k account: Max exposure ${exposure_small['limits']['max_portfolio_value']:,.2f}")
    
    # Large account
    engine_large = RiskEngine(account_balance=1000000, max_portfolio_exposure=0.50)
    exposure_large = engine_large.calculate_portfolio_exposure([])
    assert exposure_large['limits']['max_portfolio_value'] == 500000
    
    print(f"✅ $1M account: Max exposure ${exposure_large['limits']['max_portfolio_value']:,.2f}")
    
    # Verify ratio
    ratio = exposure_large['limits']['max_portfolio_value'] / exposure_small['limits']['max_portfolio_value']
    print(f"✅ Scaling ratio: {ratio:.1f}x (correct: 100x)")
    print(f"✅ Test PASSED")
    return True


def test_exposure_with_multiple_positions():
    """Test exposure calculation with multiple positions of varying sizes."""
    print("\n" + "="*80)
    print("TEST 9: Exposure - Multiple Positions")
    print("="*80)
    
    engine = RiskEngine(
        account_balance=100000,
        max_portfolio_exposure=0.60
    )
    
    # Multiple positions
    positions = [
        {'value': 10000, 'risk': 200},
        {'value': 15000, 'risk': 300},
        {'value': 12000, 'risk': 240},
        {'value': 18000, 'risk': 360},
    ]
    
    exposure = engine.calculate_portfolio_exposure(positions)
    
    assert exposure['current_exposure']['total_position_value'] == 55000
    assert exposure['current_exposure']['exposure_percentage'] == 55.0
    assert exposure['remaining_capacity']['available_position_value'] == 5000
    
    print(f"✅ 4 positions: $10k, $15k, $12k, $18k")
    print(f"✅ Total value: ${exposure['current_exposure']['total_position_value']:,.2f}")
    print(f"✅ Total exposure: {exposure['current_exposure']['exposure_percentage']:.1f}%")
    print(f"✅ Remaining: ${exposure['remaining_capacity']['available_position_value']:,.2f}")
    print(f"✅ Test PASSED")
    return True


def test_exposure_constraints_combined():
    """Test that position count and exposure limits work together."""
    print("\n" + "="*80)
    print("TEST 10: Combined Constraints - Position Count + Exposure")
    print("="*80)
    
    engine = RiskEngine(
        account_balance=100000,
        max_portfolio_exposure=0.50,
        max_open_positions=3
    )
    
    # 3 positions at $15k each = $45k (under exposure limit but at position limit)
    positions = [
        {'value': 15000, 'risk': 300},
        {'value': 15000, 'risk': 300},
        {'value': 15000, 'risk': 300},
    ]
    
    exposure = engine.calculate_portfolio_exposure(positions)
    
    assert exposure['constraints']['positions_count'] == 3
    assert exposure['constraints']['can_add_by_count'] == False  # At position limit
    assert exposure['constraints']['can_add_position'] == True   # Under exposure limit
    
    print(f"✅ Positions: {exposure['constraints']['positions_count']}/3 (limit reached)")
    print(f"✅ Exposure: ${exposure['current_exposure']['total_position_value']:,.2f}/50k (under limit)")
    print(f"✅ Can add by count: {exposure['constraints']['can_add_by_count']}")
    print(f"✅ Can add by exposure: {exposure['constraints']['can_add_position']}")
    print(f"✅ Test PASSED")
    return True


def run_all_tests():
    """Run all portfolio exposure tests."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*78 + "║")
    print("║" + "PORTFOLIO EXPOSURE TEST SUITE".center(78) + "║")
    print("║" + " "*78 + "║")
    print("╚" + "="*78 + "╝")
    
    tests = [
        test_portfolio_exposure_calculation,
        test_position_size_adjustment_no_adjustment_needed,
        test_position_size_adjustment_partial,
        test_position_size_adjustment_full_block,
        test_position_sizing_with_exposure,
        test_portfolio_exposure_different_limits,
        test_full_trade_plan_with_exposure,
        test_exposure_with_account_scaling,
        test_exposure_with_multiple_positions,
        test_exposure_constraints_combined,
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
