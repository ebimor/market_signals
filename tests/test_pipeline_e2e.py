import pytest


def test_signal_to_execution_to_close_profit_pipeline(client):
    # 1) Create signal
    create_payload = {
        "symbol": "AAPL",
        "signal_type": "BUY",
        "price": 100.0,
        "confidence": 82.0,
        "reason": "Test pipeline signal",
        "position_size": 10,
        "stop_loss": 96.0,
        "take_profit": 106.0,
        "atr": 2.0,
    }
    signal_res = client.post("/api/trading/signals", json=create_payload)
    assert signal_res.status_code == 200
    signal_id = signal_res.json()["signal_id"]

    # 2) Approve -> auto execute
    approve_res = client.post(
        "/api/trading/approve",
        json={"signal_id": signal_id, "approval_notes": "approved in test"},
    )
    assert approve_res.status_code == 200
    trade_id = approve_res.json()["trade_id"]

    # 3) Verify open trade has expected risk settings
    open_res = client.get("/api/trading/trades/open")
    assert open_res.status_code == 200
    open_trades = open_res.json()
    assert len(open_trades) == 1
    assert open_trades[0]["trade_id"] == trade_id
    assert open_trades[0]["stop_loss"] == 96.0
    assert open_trades[0]["take_profit"] == 106.0

    # 4) Close trade with profit
    close_res = client.post(
        "/api/trading/close",
        json={
            "trade_id": trade_id,
            "exit_price": 105.0,
            "exit_reason": "take profit",
        },
    )
    assert close_res.status_code == 200
    closed_trade = close_res.json()

    # Profit = (105 - 100) * 10 = 50
    assert closed_trade["status"] == "closed"
    assert closed_trade["pnl"] == pytest.approx(50.0)
    assert closed_trade["pnl_percent"] == pytest.approx(5.0)

    # 5) Stats should reflect completed profitable trade
    stats_res = client.get("/api/trading/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()

    assert stats["total_trades"] == 1
    assert stats["winning_trades"] == 1
    assert stats["losing_trades"] == 0
    assert stats["win_rate"] == pytest.approx(100.0)
    assert stats["total_pnl"] == pytest.approx(50.0)
    assert stats["total_exposure"] == pytest.approx(0.0)
    # initial_cash (100000) + total_pnl (50), no open positions
    assert stats["current_cash"] == pytest.approx(100050.0)


def test_manual_trade_pipeline_loss_stop_take_and_cash_exposure(client):
    # 1) Open manual trade
    manual_open_res = client.post(
        "/api/trading/manual",
        json={
            "symbol": "TSLA",
            "signal_type": "BUY",
            "entry_price": 200.0,
            "position_size": 5,
            "stop_loss": 190.0,
            "take_profit": 220.0,
            "notes": "manual test trade",
        },
    )
    assert manual_open_res.status_code == 200
    opened = manual_open_res.json()
    trade_id = opened["trade_id"]

    assert opened["stop_loss"] == 190.0
    assert opened["take_profit"] == 220.0

    # 2) Before closing: exposure and cash should reflect open capital
    stats_open_res = client.get("/api/trading/stats")
    stats_open = stats_open_res.json()
    # cost = 200 * 5 = 1000
    assert stats_open["total_exposure"] == pytest.approx(1000.0)
    assert stats_open["current_cash"] == pytest.approx(99000.0)

    # 3) Close with loss: (195 - 200) * 5 = -25
    manual_close_res = client.post(
        "/api/trading/close",
        json={
            "trade_id": trade_id,
            "exit_price": 195.0,
            "exit_reason": "stop loss hit",
        },
    )
    assert manual_close_res.status_code == 200
    closed = manual_close_res.json()

    assert closed["status"] == "closed"
    assert closed["pnl"] == pytest.approx(-25.0)
    assert closed["pnl_percent"] == pytest.approx(-2.5)

    # 4) After close: no exposure, cash includes realized loss
    stats_closed_res = client.get("/api/trading/stats")
    stats_closed = stats_closed_res.json()
    assert stats_closed["total_trades"] == 1
    assert stats_closed["winning_trades"] == 0
    assert stats_closed["losing_trades"] == 1
    assert stats_closed["total_pnl"] == pytest.approx(-25.0)
    assert stats_closed["total_exposure"] == pytest.approx(0.0)
    assert stats_closed["current_cash"] == pytest.approx(99975.0)
