from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import backend.api.trading as trading_api
from backend.main import app
from backend.trading.trade_manager import TradeManager


@pytest.fixture
def isolated_trade_manager(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TradeManager:
    """Use a fresh trade manager + JSON store for every test."""
    records_file = tmp_path / "trade_records_test.json"
    manager = TradeManager(records_file=str(records_file))
    monkeypatch.setattr(trading_api, "trade_manager", manager)
    return manager


@pytest.fixture
def client(isolated_trade_manager: TradeManager) -> TestClient:
    """FastAPI test client wired to isolated trade state."""
    return TestClient(app)
