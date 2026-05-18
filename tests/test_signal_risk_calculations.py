import numpy as np
import pandas as pd
import pytest

from backend.risk.risk_engine import RiskEngine
from backend.signals.indicators import RSI, SignalGenerator


def _make_ohlcv(length: int = 60, trend: float = 0.2) -> pd.DataFrame:
    """Deterministic-ish OHLCV sample for indicator tests."""
    np.random.seed(42)
    base = 100
    close = np.array([base + i * trend for i in range(length)], dtype=float)
    close = close + np.random.normal(0, 0.4, length)

    high = close * 1.01
    low = close * 0.99
    open_ = close * 0.995
    volume = np.random.randint(1_000_000, 5_000_000, length)

    return pd.DataFrame(
        {
            "Open": open_,
            "High": high,
            "Low": low,
            "Close": close,
            "Volume": volume,
        }
    )


def test_rsi_signal_and_confidence_thresholds():
    rsi = RSI(period=14)

    assert rsi.get_signal(25) == "BUY"
    assert rsi.get_signal(75) == "SELL"
    assert rsi.get_signal(50) == "HOLD"

    assert rsi.get_confidence(10) > rsi.get_confidence(30)
    assert rsi.get_confidence(90) > rsi.get_confidence(70)


def test_signal_generator_outputs_structure_and_valid_ranges():
    data = _make_ohlcv(length=80, trend=0.15)
    generator = SignalGenerator()

    result = generator.generate_signal(data)

    assert result["signal"] in {"BUY", "SELL", "HOLD"}
    assert 0 <= result["confidence"] <= 100
    assert set(result["votes"].keys()) == {"BUY", "SELL", "HOLD"}
    # RSI, MACD, EMA, BB each cast one vote
    assert sum(result["votes"].values()) == 4

    for component in ["rsi", "macd", "ema", "bb", "atr"]:
        assert component in result["components"]


def test_risk_engine_position_size_exits_and_trade_plan_metrics():
    engine = RiskEngine(
        account_balance=100000,
        risk_per_trade=0.02,
        max_position_size=0.10,
        sl_atr_multiple=2.0,
        tp_atr_multiple=3.0,
        min_reward_ratio=1.2,
    )

    sizing = engine.calculate_position_size(
        entry_price=100,
        signal_confidence=80,
        atr=2,
        signal="BUY",
        open_positions=[],
    )

    assert sizing["position_size"] > 0
    assert sizing["position_value"] <= engine.max_position_value
    assert 0 <= sizing["risk_percentage"] <= 2.0

    exits = engine.calculate_exits(entry_price=100, atr=2, signal="BUY")
    assert exits["stop_loss"] == pytest.approx(96.0)
    assert exits["take_profit"] == pytest.approx(106.0)
    assert exits["risk_per_share"] == pytest.approx(4.0)
    assert exits["reward_per_share"] == pytest.approx(6.0)
    assert exits["risk_reward_ratio"] == pytest.approx(1.5)

    plan = engine.calculate_full_trade_plan(
        entry_price=100,
        signal_confidence=80,
        atr=2,
        signal="BUY",
        ticker="AAPL",
        open_positions=[],
    )

    assert plan["ticker"] == "AAPL"
    assert plan["position"]["size"] > 0
    assert plan["metrics"]["potential_loss"] == pytest.approx(
        plan["position"]["size"] * plan["exits"]["risk_per_share"]
    )
    assert plan["metrics"]["potential_gain"] == pytest.approx(
        plan["position"]["size"] * plan["exits"]["reward_per_share"]
    )
    assert isinstance(plan["valid"], bool)
