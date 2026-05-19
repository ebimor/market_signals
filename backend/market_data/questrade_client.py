"""
Questrade API client for live market quotes.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import requests

from backend.config import settings

logger = logging.getLogger(__name__)


class QuestradeClient:
    """Minimal Questrade client for live market quotes."""

    def __init__(self, refresh_token: Optional[str] = None, persist_refresh_token: bool = True):
        self._session = requests.Session()
        self._refresh_token = refresh_token or settings.questrade_refresh_token
        self._access_token: Optional[str] = None
        self._api_server: Optional[str] = None
        self._token_expires_at: float = 0.0
        self._persist_refresh_token = persist_refresh_token
        self._symbol_cache: Dict[str, Dict[str, Any]] = {}

    @property
    def is_configured(self) -> bool:
        return bool(self._refresh_token)

    def _persist_refresh_token_to_env(self, refresh_token: str) -> None:
        if not self._persist_refresh_token:
            return

        env_path = Path(__file__).resolve().parents[1] / ".env"
        if not env_path.exists():
            return

        try:
            lines = env_path.read_text().splitlines()
            updated = False
            new_lines = []
            for line in lines:
                if line.startswith("QUESTRADE_REFRESH_TOKEN="):
                    new_lines.append(f"QUESTRADE_REFRESH_TOKEN={refresh_token}")
                    updated = True
                else:
                    new_lines.append(line)
            if not updated:
                new_lines.append(f"QUESTRADE_REFRESH_TOKEN={refresh_token}")
            env_path.write_text("\n".join(new_lines) + "\n")
        except Exception as exc:
            logger.warning("Could not persist Questrade refresh token: %s", exc)

    def _refresh_access_token(self) -> bool:
        if not self._refresh_token:
            return False

        try:
            response = self._session.get(
                "https://login.questrade.com/oauth2/token",
                params={
                    "grant_type": "refresh_token",
                    "refresh_token": self._refresh_token,
                },
                timeout=20,
            )
            if response.status_code != 200:
                logger.warning("Questrade auth failed: %s %s", response.status_code, response.text[:200])
                return False

            payload = response.json()
            self._access_token = payload.get("access_token")
            self._api_server = str(payload.get("api_server", "")).rstrip("/") or None
            self._token_expires_at = time.time() + max(int(payload.get("expires_in", 0)) - 60, 60)

            new_refresh_token = payload.get("refresh_token")
            if new_refresh_token:
                self._refresh_token = new_refresh_token
                self._persist_refresh_token_to_env(new_refresh_token)
                settings.questrade_refresh_token = new_refresh_token

            return bool(self._access_token and self._api_server)
        except Exception as exc:
            logger.warning("Questrade auth error: %s", exc)
            return False

    def _ensure_token(self) -> bool:
        if self._access_token and self._api_server and time.time() < self._token_expires_at:
            return True
        return self._refresh_access_token()

    def _request_json(self, path: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        if not self._ensure_token() or not self._api_server or not self._access_token:
            return None

        url = f"{self._api_server}{path}"
        headers = {"Authorization": f"Bearer {self._access_token}"}

        try:
            response = self._session.get(url, params=params, headers=headers, timeout=20)
            if response.status_code == 401 and self._refresh_access_token():
                headers = {"Authorization": f"Bearer {self._access_token}"}
                response = self._session.get(url, params=params, headers=headers, timeout=20)

            if response.status_code >= 400:
                logger.warning("Questrade request failed: %s %s", response.status_code, response.text[:200])
                return None

            return response.json()
        except Exception as exc:
            logger.warning("Questrade request error for %s: %s", path, exc)
            return None

    def search_symbol(self, ticker: str) -> Optional[Dict[str, Any]]:
        symbol = ticker.upper().strip()
        if symbol in self._symbol_cache:
            return self._symbol_cache[symbol]

        payload = self._request_json("/v1/symbols/search", params={"prefix": symbol})
        if not payload:
            return None

        matches = payload.get("symbols", []) or []
        if not matches:
            return None

        exact = next((item for item in matches if item.get("symbol", "").upper() == symbol), matches[0])
        self._symbol_cache[symbol] = exact
        return exact

    def get_quote(self, ticker: str) -> Optional[Dict[str, Any]]:
        symbol_info = self.search_symbol(ticker)
        if not symbol_info:
            return None

        symbol_id = symbol_info.get("symbolId")
        if symbol_id is None:
            return None

        payload = self._request_json("/v1/markets/quotes", params={"ids": str(symbol_id)})
        if not payload:
            return None

        quotes = payload.get("quotes", []) or []
        if not quotes:
            return None

        quote = quotes[0]
        return {
            "symbol": quote.get("symbol", ticker.upper()),
            "symbol_id": quote.get("symbolId", symbol_id),
            "last_trade_price": quote.get("lastTradePrice"),
            "bid_price": quote.get("bidPrice"),
            "ask_price": quote.get("askPrice"),
            "last_trade_time": quote.get("lastTradeTime"),
            "quote": quote,
        }

    def get_current_price(self, ticker: str) -> Optional[float]:
        quote = self.get_quote(ticker)
        if quote is None:
            return None

        last_trade_price = quote.get("last_trade_price")
        if last_trade_price is not None:
            try:
                return float(last_trade_price)
            except (TypeError, ValueError):
                pass

        bid_price = quote.get("bid_price")
        ask_price = quote.get("ask_price")
        try:
            if bid_price is not None and ask_price is not None:
                return float((float(bid_price) + float(ask_price)) / 2)
            if bid_price is not None:
                return float(bid_price)
            if ask_price is not None:
                return float(ask_price)
        except (TypeError, ValueError):
            return None

        return None

    def get_historical_data(self, ticker: str, period: str = "3mo", interval: str = "1d") -> Optional[pd.DataFrame]:
        """Fetch historical OHLCV candles from Questrade."""
        symbol_info = self.search_symbol(ticker)
        if not symbol_info:
            return None

        symbol_id = symbol_info.get("symbolId")
        if symbol_id is None:
            return None

        interval_map = {
            "1m": "OneMinute",
            "5m": "FiveMinutes",
            "15m": "FifteenMinutes",
            "30m": "HalfHour",
            "60m": "OneHour",
            "1d": "OneDay",
            "1wk": "OneWeek",
            "1mo": "OneMonth",
        }
        qt_interval = interval_map.get(interval, "OneDay")

        days_map = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
            "2y": 730,
            "5y": 1825,
            "10y": 3650,
            "ytd": 365,
            "max": 3650,
        }
        lookback_days = days_map.get(period, 90)

        now = datetime.now(timezone.utc)
        start = now - timedelta(days=lookback_days)

        def _qt_time(ts: datetime) -> str:
            # Questrade candles endpoint expects timezone-aware ISO timestamp.
            # Use whole seconds and explicit UTC offset marker.
            return ts.replace(microsecond=0).isoformat().replace("+00:00", "-00:00")

        payload = self._request_json(
            f"/v1/markets/candles/{symbol_id}",
            params={
                "startTime": _qt_time(start),
                "endTime": _qt_time(now),
                "interval": qt_interval,
            },
        )
        if not payload:
            return None

        candles = payload.get("candles", []) or []
        if not candles:
            return None

        rows = []
        for candle in candles:
            ts = candle.get("end") or candle.get("start")
            if ts is None:
                continue

            rows.append(
                {
                    "timestamp": pd.to_datetime(ts),
                    "open": candle.get("open"),
                    "high": candle.get("high"),
                    "low": candle.get("low"),
                    "close": candle.get("close"),
                    "volume": candle.get("volume"),
                }
            )

        if not rows:
            return None

        df = pd.DataFrame(rows).dropna(subset=["timestamp", "open", "high", "low", "close"])
        if df.empty:
            return None

        df = df.set_index("timestamp").sort_index()
        return df