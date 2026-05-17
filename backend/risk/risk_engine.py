"""
Risk Management Engine

Calculates position sizing, stop-loss, take-profit levels, and portfolio allocation
based on signal confidence, volatility (ATR), and account balance.

Key Features:
- Kelly Criterion-based position sizing (conservative)
- ATR-based stop-loss (2x ATR default)
- ATR-based take-profit (3x ATR default)
- Risk-reward ratio validation (minimum 1:2)
- Portfolio allocation to diversify across positions
- Maximum position size per trade (risk limit)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class RiskEngine:
    """
    Comprehensive risk management system for position sizing and exit planning.
    
    Algorithm Flow:
    1. Calculate risk per trade as % of account (typically 1-2%)
    2. Use signal confidence to adjust position size (higher confidence = larger position)
    3. Set stop-loss using ATR (2x ATR below entry for uptrends)
    4. Set take-profit using ATR (3x ATR above entry for uptrends)
    5. Validate risk-reward ratio (TP should be > SL with minimum 1:2)
    6. Apply position size limits and portfolio allocation
    """
    
    def __init__(
        self,
        account_balance: float = 100000,
        risk_per_trade: float = 0.02,  # 2% risk per trade
        max_position_size: float = 0.10,  # 10% of account per trade
        max_portfolio_exposure: float = 0.50,  # 50% max total exposure
        sl_atr_multiple: float = 2.0,  # Stop-loss at 2x ATR
        tp_atr_multiple: float = 3.0,  # Take-profit at 3x ATR
        min_reward_ratio: float = 2.0,  # Minimum 1:2 risk-reward
        max_open_positions: int = 5,  # Maximum concurrent positions
    ):
        """
        Initialize Risk Engine.
        
        Args:
            account_balance: Total account balance in USD
            risk_per_trade: Percentage of account to risk per trade (0.01 = 1%)
            max_position_size: Maximum position size as % of account per trade
            max_portfolio_exposure: Maximum total portfolio exposure (0.50 = 50% max deployed)
            sl_atr_multiple: Stop-loss distance in ATR multiples
            tp_atr_multiple: Take-profit distance in ATR multiples
            min_reward_ratio: Minimum reward/risk ratio (e.g., 2.0 = 1:2)
            max_open_positions: Maximum number of concurrent open positions
        """
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade
        self.max_position_size = max_position_size
        self.max_portfolio_exposure = max_portfolio_exposure
        self.sl_atr_multiple = sl_atr_multiple
        self.tp_atr_multiple = tp_atr_multiple
        self.min_reward_ratio = min_reward_ratio
        self.max_open_positions = max_open_positions
        
        # Derived values
        self.risk_amount = account_balance * risk_per_trade  # USD to risk
        self.max_position_value = account_balance * max_position_size  # Max USD per trade
        self.max_portfolio_value = account_balance * max_portfolio_exposure  # Max total deployed
        
        logger.info(f"""
        RiskEngine initialized:
        - Account Balance: ${account_balance:,.2f}
        - Risk Per Trade: {risk_per_trade*100:.1f}% (${self.risk_amount:,.2f})
        - Max Position Size: {max_position_size*100:.1f}% (${self.max_position_value:,.2f})
        - Max Portfolio Exposure: {max_portfolio_exposure*100:.1f}% (${self.max_portfolio_value:,.2f})
        - SL Multiple: {sl_atr_multiple}x ATR
        - TP Multiple: {tp_atr_multiple}x ATR
        - Min Reward Ratio: 1:{min_reward_ratio}
        - Max Open Positions: {max_open_positions}
        """)
    
    def calculate_position_size(
        self,
        entry_price: float,
        signal_confidence: float,
        atr: float,
        signal: str = "BUY"
    ) -> Dict[str, float]:
        """
        Calculate position size based on Kelly Criterion (simplified) and signal confidence.
        
        Position sizing approach:
        1. Calculate shares from risk amount and ATR-based stop-loss
        2. Adjust for signal confidence (higher confidence = larger position)
        3. Cap at max position size
        
        Args:
            entry_price: Entry price (current price)
            signal_confidence: Confidence 0-100
            atr: Average True Range value
            signal: "BUY" or "SELL"
        
        Returns:
            Dict with position_size, position_value, risk_amount
        """
        if entry_price <= 0 or atr <= 0:
            logger.warning(f"Invalid entry_price ({entry_price}) or atr ({atr})")
            return {
                "position_size": 0,
                "position_value": 0,
                "risk_amount": 0,
                "risk_percentage": 0,
            }
        
        # Calculate stop-loss distance
        sl_distance = atr * self.sl_atr_multiple
        
        # Calculate shares: how many shares can we buy with our risk amount?
        # position_size = risk_amount / stop_loss_distance (in price per share)
        max_shares_by_risk = self.risk_amount / sl_distance if sl_distance > 0 else 0
        
        # Cap by maximum position value (regardless of confidence)
        max_shares_by_value = self.max_position_value / entry_price if entry_price > 0 else 0
        
        # Base position size (smaller of risk-based or value-based)
        base_position = min(max_shares_by_risk, max_shares_by_value)
        
        # Adjust for signal confidence (50-100 → 0.5-1.0 multiplier)
        confidence_multiplier = (signal_confidence / 100.0) * 0.5 + 0.5  # 0.5 at 0%, 1.0 at 100%
        
        # Apply confidence adjustment, but cap at base position
        position_size = base_position * confidence_multiplier
        
        # Round to whole shares
        position_size = int(position_size)
        
        # Calculate actual position value and risk
        position_value = position_size * entry_price
        actual_risk = position_size * sl_distance
        
        result = {
            "position_size": position_size,
            "position_value": position_value,
            "risk_amount": min(actual_risk, self.risk_amount),
            "risk_percentage": (actual_risk / self.account_balance * 100) if self.account_balance > 0 else 0,
            "confidence_multiplier": confidence_multiplier,
            "max_shares_by_risk": int(max_shares_by_risk),
            "max_shares_by_value": int(max_shares_by_value),
        }
        
        logger.info(f"""
        Position Sizing:
        - Entry Price: ${entry_price:.2f}
        - Signal Confidence: {signal_confidence:.1f}%
        - ATR: ${atr:.2f}
        - SL Distance: ${sl_distance:.2f}
        - Position Size: {position_size} shares (${position_value:,.2f})
        - Risk Amount: ${actual_risk:,.2f} ({result['risk_percentage']:.2f}% of account)
        """)
        
        return result
    
    def calculate_portfolio_exposure(
        self,
        open_positions: List[Dict] = None
    ) -> Dict:
        """
        Calculate current and remaining portfolio exposure.
        
        Tracks total capital deployed across all open positions and remaining capacity.
        
        Args:
            open_positions: List of open position dicts with 'value' and 'risk' keys
        
        Returns:
            Dict with exposure details and constraints
        """
        if open_positions is None:
            open_positions = []
        
        # Calculate current exposure
        total_position_value = sum(p.get('value', 0) for p in open_positions)
        total_risk_deployed = sum(p.get('risk', 0) for p in open_positions)
        
        # Calculate percentages
        exposure_pct = (total_position_value / self.account_balance * 100) if self.account_balance > 0 else 0
        risk_pct = (total_risk_deployed / self.account_balance * 100) if self.account_balance > 0 else 0
        
        # Calculate remaining capacity
        remaining_position_value = self.max_portfolio_value - total_position_value
        remaining_exposure_pct = (remaining_position_value / self.account_balance * 100) if self.account_balance > 0 else 0
        
        # Check if at limits
        at_exposure_limit = total_position_value >= self.max_portfolio_value
        can_add_position = remaining_position_value > 0
        
        return {
            "current_exposure": {
                "total_position_value": round(total_position_value, 2),
                "total_risk_deployed": round(total_risk_deployed, 2),
                "exposure_percentage": round(exposure_pct, 2),
                "risk_percentage": round(risk_pct, 2),
            },
            "limits": {
                "max_portfolio_value": round(self.max_portfolio_value, 2),
                "max_exposure_percentage": round(self.max_portfolio_exposure * 100, 2),
            },
            "remaining_capacity": {
                "available_position_value": round(remaining_position_value, 2),
                "available_exposure_percentage": round(remaining_exposure_pct, 2),
            },
            "constraints": {
                "at_exposure_limit": at_exposure_limit,
                "can_add_position": can_add_position,
                "positions_count": len(open_positions),
                "can_add_by_count": len(open_positions) < self.max_open_positions,
            },
        }
    
    def adjust_position_size_for_exposure(
        self,
        position_size: int,
        entry_price: float,
        open_positions: List[Dict] = None
    ) -> Dict:
        """
        Adjust position size based on remaining portfolio exposure capacity.
        
        If adding this position would exceed max exposure, reduce position size proportionally.
        
        Args:
            position_size: Proposed position size (shares)
            entry_price: Entry price per share
            open_positions: List of open position dicts
        
        Returns:
            Dict with adjusted position, reduction info, and constraints
        """
        if open_positions is None:
            open_positions = []
        
        proposed_value = position_size * entry_price
        exposure = self.calculate_portfolio_exposure(open_positions)
        
        available_capacity = exposure['remaining_capacity']['available_position_value']
        at_limit = exposure['constraints']['at_exposure_limit']
        
        # If at limit, can't add position
        if at_limit:
            return {
                "original_position_size": position_size,
                "adjusted_position_size": 0,
                "original_position_value": round(proposed_value, 2),
                "adjusted_position_value": 0,
                "reduction_percentage": 100,
                "reduction_reason": "Maximum portfolio exposure limit reached",
                "was_adjusted": True,
            }
        
        # If proposed position exceeds available capacity, reduce it
        if proposed_value > available_capacity:
            reduction_ratio = available_capacity / proposed_value if proposed_value > 0 else 0
            adjusted_size = int(position_size * reduction_ratio)
            adjusted_value = adjusted_size * entry_price
            reduction_pct = (1 - reduction_ratio) * 100
            
            return {
                "original_position_size": position_size,
                "adjusted_position_size": adjusted_size,
                "original_position_value": round(proposed_value, 2),
                "adjusted_position_value": round(adjusted_value, 2),
                "reduction_percentage": round(reduction_pct, 2),
                "reduction_reason": f"Limited by portfolio exposure cap (${available_capacity:,.2f} available)",
                "was_adjusted": True,
            }
        
        # No adjustment needed
        return {
            "original_position_size": position_size,
            "adjusted_position_size": position_size,
            "original_position_value": round(proposed_value, 2),
            "adjusted_position_value": round(proposed_value, 2),
            "reduction_percentage": 0,
            "reduction_reason": "None - within exposure limits",
            "was_adjusted": False,
        }
    
    def calculate_position_size(
        self,
        entry_price: float,
        signal_confidence: float,
        atr: float,
        signal: str = "BUY",
        open_positions: List[Dict] = None
    ) -> Dict[str, float]:
        """
        Calculate position size based on Kelly Criterion (simplified) and signal confidence.
        
        Position sizing approach:
        1. Calculate shares from risk amount and ATR-based stop-loss
        2. Adjust for signal confidence (higher confidence = larger position)
        3. Cap at max position size
        4. Adjust for remaining portfolio exposure capacity
        
        Args:
            entry_price: Entry price (current price)
            signal_confidence: Confidence 0-100
            atr: Average True Range value
            signal: "BUY" or "SELL"
            open_positions: List of currently open positions (for exposure calculation)
        
        Returns:
            Dict with position_size, position_value, risk_amount, and exposure info
        """
        if open_positions is None:
            open_positions = []
            
        if entry_price <= 0 or atr <= 0:
            logger.warning(f"Invalid entry_price ({entry_price}) or atr ({atr})")
            return {
                "position_size": 0,
                "position_value": 0,
                "risk_amount": 0,
                "risk_percentage": 0,
                "portfolio_exposure": self.calculate_portfolio_exposure(open_positions),
                "exposure_adjustment": {
                    "was_adjusted": False,
                    "reduction_reason": "Invalid entry price or ATR",
                }
            }
        
        # Calculate stop-loss distance
        sl_distance = atr * self.sl_atr_multiple
        
        # Calculate shares: how many shares can we buy with our risk amount?
        # position_size = risk_amount / stop_loss_distance (in price per share)
        max_shares_by_risk = self.risk_amount / sl_distance if sl_distance > 0 else 0
        
        # Cap by maximum position value (regardless of confidence)
        max_shares_by_value = self.max_position_value / entry_price if entry_price > 0 else 0
        
        # Base position size (smaller of risk-based or value-based)
        base_position = min(max_shares_by_risk, max_shares_by_value)
        
        # Adjust for signal confidence (50-100 → 0.5-1.0 multiplier)
        confidence_multiplier = (signal_confidence / 100.0) * 0.5 + 0.5  # 0.5 at 0%, 1.0 at 100%
        
        # Apply confidence adjustment, but cap at base position
        position_size = base_position * confidence_multiplier
        
        # Round to whole shares
        position_size = int(position_size)
        
        # Adjust for portfolio exposure limits
        exposure_adjustment = self.adjust_position_size_for_exposure(
            position_size, entry_price, open_positions
        )
        final_position_size = exposure_adjustment['adjusted_position_size']
        
        # Calculate actual position value and risk
        position_value = final_position_size * entry_price
        actual_risk = final_position_size * sl_distance
        
        result = {
            "position_size": final_position_size,
            "position_value": position_value,
            "risk_amount": min(actual_risk, self.risk_amount),
            "risk_percentage": (actual_risk / self.account_balance * 100) if self.account_balance > 0 else 0,
            "confidence_multiplier": confidence_multiplier,
            "max_shares_by_risk": int(max_shares_by_risk),
            "max_shares_by_value": int(max_shares_by_value),
            "base_position_size": int(base_position),
            "portfolio_exposure": self.calculate_portfolio_exposure(open_positions),
            "exposure_adjustment": {
                "was_adjusted": exposure_adjustment['was_adjusted'],
                "original_size": exposure_adjustment['original_position_size'],
                "adjusted_size": exposure_adjustment['adjusted_position_size'],
                "reduction_percentage": exposure_adjustment['reduction_percentage'],
                "reduction_reason": exposure_adjustment['reduction_reason'],
            }
        }
        
        logger.info(f"""
        Position Sizing (with Portfolio Exposure):
        - Entry Price: ${entry_price:.2f}
        - Signal Confidence: {signal_confidence:.1f}%
        - ATR: ${atr:.2f}
        - Position Size: {final_position_size} shares (${position_value:,.2f})
        - Risk Amount: ${actual_risk:,.2f} ({result['risk_percentage']:.2f}% of account)
        - Portfolio Exposure: {exposure_adjustment['was_adjusted'] and 'ADJUSTED' or 'OK'}
        """)
        
        return result
    
    def calculate_exits(
        self,
        entry_price: float,
        atr: float,
        signal: str = "BUY"
    ) -> Dict[str, float]:
        """
        Calculate stop-loss and take-profit levels using ATR multiples.
        
        Exit Strategy:
        - Stop-Loss: entry_price - (sl_atr_multiple × ATR) for BUY
        - Take-Profit: entry_price + (tp_atr_multiple × ATR) for BUY
        - Reversed for SELL signals
        
        Args:
            entry_price: Entry price
            atr: Average True Range value
            signal: "BUY" or "SELL"
        
        Returns:
            Dict with stop_loss, take_profit, risk_amount, reward_amount, risk_reward_ratio
        """
        if entry_price <= 0 or atr <= 0:
            logger.warning(f"Invalid entry_price ({entry_price}) or atr ({atr})")
            return {
                "stop_loss": 0,
                "take_profit": 0,
                "risk_amount": 0,
                "reward_amount": 0,
                "risk_reward_ratio": 0,
                "valid": False,
            }
        
        sl_distance = atr * self.sl_atr_multiple
        tp_distance = atr * self.tp_atr_multiple
        
        if signal.upper() == "BUY":
            stop_loss = entry_price - sl_distance
            take_profit = entry_price + tp_distance
        elif signal.upper() == "SELL":
            stop_loss = entry_price + sl_distance
            take_profit = entry_price - tp_distance
        else:
            logger.warning(f"Invalid signal: {signal}")
            return {
                "stop_loss": 0,
                "take_profit": 0,
                "risk_amount": 0,
                "reward_amount": 0,
                "risk_reward_ratio": 0,
                "valid": False,
            }
        
        # Calculate risk and reward per share
        risk_per_share = abs(entry_price - stop_loss)
        reward_per_share = abs(take_profit - entry_price)
        
        # Calculate risk-reward ratio
        risk_reward_ratio = reward_per_share / risk_per_share if risk_per_share > 0 else 0
        
        # Validate minimum reward ratio
        valid = risk_reward_ratio >= self.min_reward_ratio
        
        result = {
            "entry_price": entry_price,
            "stop_loss": round(stop_loss, 4),
            "take_profit": round(take_profit, 4),
            "risk_per_share": round(risk_per_share, 4),
            "reward_per_share": round(reward_per_share, 4),
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "valid": valid,
            "atr_multiple_sl": self.sl_atr_multiple,
            "atr_multiple_tp": self.tp_atr_multiple,
        }
        
        logger.info(f"""
        Exit Levels ({signal.upper()}):
        - Entry: ${entry_price:.2f}
        - Stop Loss: ${stop_loss:.2f} (risk: ${risk_per_share:.2f}/share)
        - Take Profit: ${take_profit:.2f} (reward: ${reward_per_share:.2f}/share)
        - Risk/Reward Ratio: 1:{risk_reward_ratio:.2f} (Valid: {valid})
        """)
        
        return result
    
    def calculate_full_trade_plan(
        self,
        entry_price: float,
        signal_confidence: float,
        atr: float,
        signal: str = "BUY",
        ticker: str = None,
        open_positions: List[Dict] = None
    ) -> Dict:
        """
        Generate complete trade plan combining position sizing and exits.
        
        Returns comprehensive trade details including:
        - Position size and value
        - Stop-loss and take-profit levels
        - Risk amount and risk-reward ratio
        - Portfolio allocation recommendation
        - Portfolio exposure information
        
        Args:
            entry_price: Current price (entry point)
            signal_confidence: Signal confidence 0-100
            atr: Average True Range
            signal: "BUY" or "SELL"
            ticker: Ticker symbol (for logging)
            open_positions: List of currently open positions
        
        Returns:
            Complete trade plan dictionary
        """
        if open_positions is None:
            open_positions = []
            
        # Calculate position sizing (with portfolio exposure consideration)
        position = self.calculate_position_size(entry_price, signal_confidence, atr, signal, open_positions)
        
        # Calculate exits
        exits = self.calculate_exits(entry_price, atr, signal)
        
        # Combine into full trade plan
        trade_plan = {
            "ticker": ticker or "UNKNOWN",
            "signal": signal.upper(),
            "confidence": signal_confidence,
            "entry_price": entry_price,
            "atr": round(atr, 4),
            "position": {
                "size": position["position_size"],
                "value": round(position["position_value"], 2),
                "risk_amount": round(position["risk_amount"], 2),
                "risk_percentage": round(position["risk_percentage"], 2),
            },
            "exits": {
                "stop_loss": exits["stop_loss"],
                "take_profit": exits["take_profit"],
                "risk_per_share": exits["risk_per_share"],
                "reward_per_share": exits["reward_per_share"],
                "risk_reward_ratio": exits["risk_reward_ratio"],
            },
            "metrics": {
                "potential_loss": round(position["position_size"] * exits["risk_per_share"], 2),
                "potential_gain": round(position["position_size"] * exits["reward_per_share"], 2),
                "breakeven": round(entry_price, 4),
                "expected_value": round(
                    position["position_size"] * exits["reward_per_share"] * (signal_confidence / 100)
                    - position["position_size"] * exits["risk_per_share"] * (1 - signal_confidence / 100),
                    2
                ),
            },
            "portfolio_exposure": position.get("portfolio_exposure", {}),
            "exposure_adjustment": position.get("exposure_adjustment", {}),
            "valid": exits["valid"] and position["position_size"] > 0,
        }
        
        return trade_plan
    
    def calculate_portfolio_allocation(
        self,
        open_positions: int = 0,
        new_signal_confidence: float = 0
    ) -> Dict:
        """
        Calculate portfolio allocation recommendations for diversification.
        
        Strategy:
        - Each position gets equal allocation (1/max_open_positions of account)
        - Can reduce if max positions reached
        - Can boost allocation for high-confidence signals if slots available
        
        Args:
            open_positions: Number of currently open positions
            new_signal_confidence: Confidence of new potential position
        
        Returns:
            Dict with allocation details and recommendations
        """
        can_open_new = open_positions < self.max_open_positions
        slots_available = self.max_open_positions - open_positions
        
        # Base allocation per position
        base_allocation = self.account_balance / self.max_open_positions
        
        # Risk allocation
        base_risk_per_position = self.account_balance * self.risk_per_trade
        
        # Adjustment for confidence (if we can take new position)
        if can_open_new and new_signal_confidence > 50:
            confidence_boost = (new_signal_confidence - 50) / 50  # 0-1 scale
            recommended_risk = base_risk_per_position * (1 + confidence_boost * 0.5)  # +50% max boost
        else:
            recommended_risk = base_risk_per_position
        
        allocation = {
            "can_open_new_position": can_open_new,
            "slots_available": slots_available,
            "open_positions": open_positions,
            "max_positions": self.max_open_positions,
            "base_allocation_per_position": round(base_allocation, 2),
            "recommended_risk_amount": round(recommended_risk, 2),
            "recommended_position_size": round(self.max_position_value, 2),
            "total_account_at_max_allocation": round(base_allocation * self.max_open_positions, 2),
            "remaining_cash": round(self.account_balance - (open_positions * base_allocation), 2),
        }
        
        logger.info(f"""
        Portfolio Allocation:
        - Open: {open_positions}/{self.max_open_positions}
        - Slots Available: {slots_available}
        - Base Risk per Position: ${base_risk_per_position:,.2f}
        - Recommended Risk (adjusted): ${recommended_risk:,.2f}
        - Can Open New: {can_open_new}
        """)
        
        return allocation
    
    def get_max_drawdown_limit(self) -> Dict:
        """
        Calculate maximum drawdown limits for account protection.
        
        Returns:
            Dict with various drawdown limits
        """
        return {
            "daily_loss_limit": round(self.account_balance * 0.02, 2),  # 2% daily loss stop
            "weekly_loss_limit": round(self.account_balance * 0.05, 2),  # 5% weekly loss stop
            "monthly_loss_limit": round(self.account_balance * 0.10, 2),  # 10% monthly loss stop
            "account_stop_loss": round(self.account_balance * 0.20, 2),  # 20% account stop-loss
        }
    
    def validate_trade(self, trade_plan: Dict) -> Tuple[bool, List[str]]:
        """
        Validate trade plan against risk rules.
        
        Checks:
        1. Position size > 0
        2. Risk-reward ratio valid
        3. Position size doesn't exceed max
        4. Risk amount doesn't exceed per-trade limit
        
        Args:
            trade_plan: Trade plan dictionary from calculate_full_trade_plan
        
        Returns:
            Tuple of (is_valid, list_of_warnings)
        """
        warnings = []
        
        if trade_plan["position"]["size"] <= 0:
            warnings.append("Position size is 0")
        
        if not trade_plan["exits"]["risk_reward_ratio"] >= self.min_reward_ratio:
            warnings.append(
                f"Risk-reward ratio {trade_plan['exits']['risk_reward_ratio']:.2f} "
                f"is below minimum {self.min_reward_ratio:.2f}"
            )
        
        if trade_plan["position"]["value"] > self.max_position_value:
            warnings.append(
                f"Position value ${trade_plan['position']['value']:,.2f} "
                f"exceeds maximum ${self.max_position_value:,.2f}"
            )
        
        if trade_plan["position"]["risk_amount"] > self.risk_amount:
            warnings.append(
                f"Risk amount ${trade_plan['position']['risk_amount']:,.2f} "
                f"exceeds per-trade limit ${self.risk_amount:,.2f}"
            )
        
        is_valid = len(warnings) == 0 and not trade_plan.get("valid", False) == False
        
        return is_valid, warnings


# ============================================================================
# Utility Functions
# ============================================================================

def generate_sample_risk_analysis(
    ticker: str,
    price: float,
    atr: float,
    confidence: float,
    signal: str = "BUY",
    account_balance: float = 100000
) -> Dict:
    """
    Generate sample risk analysis for demonstration.
    
    Args:
        ticker: Stock ticker
        price: Current price
        atr: Average True Range
        confidence: Signal confidence 0-100
        signal: BUY or SELL
        account_balance: Account size
    
    Returns:
        Complete analysis dictionary
    """
    engine = RiskEngine(account_balance=account_balance)
    
    trade_plan = engine.calculate_full_trade_plan(
        entry_price=price,
        signal_confidence=confidence,
        atr=atr,
        signal=signal,
        ticker=ticker
    )
    
    portfolio = engine.calculate_portfolio_allocation(open_positions=2, new_signal_confidence=confidence)
    
    drawdown = engine.get_max_drawdown_limit()
    
    is_valid, warnings = engine.validate_trade(trade_plan)
    
    return {
        "ticker": ticker,
        "trade_plan": trade_plan,
        "portfolio_allocation": portfolio,
        "drawdown_limits": drawdown,
        "validation": {
            "is_valid": is_valid,
            "warnings": warnings,
        },
    }
