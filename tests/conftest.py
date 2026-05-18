from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient


def _find_project_root(start: Path) -> Path:
    """Find the nearest directory that contains backend/.

    Works for layouts like:
    - <repo>/backend
    - <repo>/safeswing_trader/backend
    """
    for candidate in [start, *start.parents]:
        if (candidate / "backend").is_dir():
            return candidate

        # Support one nested app folder under repo root
        for child in candidate.iterdir() if candidate.is_dir() else []:
            if child.is_dir() and (child / "backend").is_dir():
                return child

    raise RuntimeError(
        "Could not locate project root containing 'backend/' from tests/conftest.py"
    )


PROJECT_ROOT = _find_project_root(Path(__file__).resolve().parent)
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
