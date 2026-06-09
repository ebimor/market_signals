#!/usr/bin/env python3
"""
Plot RSI for the 4-hour and weekly timeframes in separate, titled charts and a
price chart that highlights the current drawdown versus the all-time high.

What it shows
-------------
1. Price chart  : close price, the running all-time-high envelope and (when the
                  stock is trading below its peak) the percentage drawdown from
                  the all-time high.
2. 4-Hour RSI   : RSI(14) built from 60-minute bars resampled to 4 hours.
3. Weekly RSI   : RSI(14) built from weekly bars.

Usage
-----
    python plot_rsi_drawdown.py [TICKER] [--show]

Examples
--------
    python plot_rsi_drawdown.py AAPL
    python plot_rsi_drawdown.py TSLA --show

The chart is always saved as a PNG next to this script. Pass ``--show`` to also
open an interactive window (requires a display).
"""
from __future__ import annotations

import sys
from pathlib import Path

# Reuse the project's RSI implementation so the chart matches the rest of the app.
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import matplotlib  # noqa: E402

# Decide on the backend before importing pyplot: only use an interactive
# backend when the user explicitly asks to display the window.
SHOW = "--show" in sys.argv
if not SHOW:
    matplotlib.use("Agg")

import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import yfinance as yf  # noqa: E402

from signals.indicators import RSI  # noqa: E402

# --- Configuration ---------------------------------------------------------
RSI_PERIOD = 14
OVERBOUGHT = 70
OVERSOLD = 30

# Data windows for each timeframe.
FOUR_HOUR = {"period": "3mo", "interval": "60m", "resample_rule": "4h"}
WEEKLY = {"period": "2y", "interval": "1wk", "resample_rule": None}
# Use the full available history so the "all-time high" is a true all-time high.
PRICE_HISTORY = {"period": "max", "interval": "1d", "resample_rule": None}

DEFAULT_TICKER = "AAPL"

# Offline fallback: the app's on-disk OHLCV cache ({TICKER}_{interval}.csv).
CACHE_DIR = BACKEND_DIR / "data" / "cache"


# --- Data helpers ----------------------------------------------------------
def _flatten_columns(data: pd.DataFrame) -> pd.DataFrame:
    """yfinance may return MultiIndex columns even for a single ticker."""
    if isinstance(data.columns, pd.MultiIndex):
        data = data.copy()
        data.columns = data.columns.get_level_values(0)
    return data


def _download_live(ticker: str, period: str, interval: str) -> pd.Series:
    """Try to fetch a Close-price Series from yfinance; empty Series on failure."""
    try:
        data = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
        )
    except Exception as exc:  # noqa: BLE001 - network/parse errors are expected
        print(f"  live fetch failed for {interval}: {exc}")
        return pd.Series(dtype=float)

    if data is None or data.empty:
        return pd.Series(dtype=float)

    data = _flatten_columns(data)
    if "Close" not in data.columns:
        return pd.Series(dtype=float)

    close = data["Close"].copy()
    close.index = pd.to_datetime(close.index)
    return close.sort_index().dropna()


def _load_cache(ticker: str, interval: str) -> pd.Series:
    """Load a Close-price Series from the app's on-disk cache, if present."""
    path = CACHE_DIR / f"{ticker}_{interval}.csv"
    if not path.exists():
        return pd.Series(dtype=float)
    try:
        df = pd.read_csv(path)
    except Exception:  # noqa: BLE001
        return pd.Series(dtype=float)
    if "close" not in df.columns or "timestamp" not in df.columns:
        return pd.Series(dtype=float)

    # The cache mixes plain daily stamps with a microsecond-precision "latest"
    # row, so parse with format="mixed" and drop anything unparseable.
    index = pd.to_datetime(df["timestamp"], utc=True, format="mixed", errors="coerce")
    close = pd.Series(pd.to_numeric(df["close"], errors="coerce").values, index=index)
    close = close[close.index.notna()]
    if not close.empty:
        close.index = close.index.tz_convert(None)  # drop tz for clean plotting
    return close.sort_index().dropna()


def get_close_series(
    ticker: str,
    period: str,
    interval: str,
    resample_rule: str | None = None,
) -> tuple[pd.Series, str]:
    """Return (Close Series, source) where source is 'live', 'cache' or 'none'.

    Falls back to the app's on-disk cache when the live download is empty
    (e.g. Yahoo rate-limiting or no network).
    """
    close = _download_live(ticker, period, interval)
    source = "live"
    if close.empty:
        close = _load_cache(ticker, interval)
        source = "cache" if not close.empty else "none"

    if not close.empty and resample_rule:
        close = close.resample(resample_rule).last().dropna()

    return close, source


def compute_rsi(close: pd.Series) -> pd.Series:
    """RSI(14) using the project's indicator, with warm-up NaNs removed."""
    if close.empty:
        return pd.Series(dtype=float)
    rsi = RSI(period=RSI_PERIOD).calculate(close)
    return rsi.dropna()


# --- Plot helpers ----------------------------------------------------------
def plot_rsi(ax, rsi: pd.Series, title: str) -> None:
    """Render an RSI(14) subchart with overbought/oversold guides and a title."""
    ax.set_title(title, fontweight="bold", fontsize=12)
    ax.set_ylabel("RSI")
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 30, 50, 70, 100])

    if rsi.empty:
        ax.text(
            0.5,
            0.5,
            "No data available",
            ha="center",
            va="center",
            transform=ax.transAxes,
            color="#a0aec0",
        )
        return

    ax.plot(rsi.index, rsi.values, color="#2b6cb0", linewidth=1.4, label=f"RSI({RSI_PERIOD})")
    ax.axhline(OVERBOUGHT, color="#e53e3e", linestyle="--", linewidth=1, label="Overbought (70)")
    ax.axhline(OVERSOLD, color="#38a169", linestyle="--", linewidth=1, label="Oversold (30)")
    ax.axhline(50, color="#a0aec0", linestyle=":", linewidth=0.8)
    ax.fill_between(rsi.index, OVERBOUGHT, 100, color="#e53e3e", alpha=0.06)
    ax.fill_between(rsi.index, 0, OVERSOLD, color="#38a169", alpha=0.06)

    latest = float(rsi.iloc[-1])
    if latest >= OVERBOUGHT:
        dot_color, zone = "#e53e3e", "Overbought"
    elif latest <= OVERSOLD:
        dot_color, zone = "#38a169", "Oversold"
    else:
        dot_color, zone = "#2b6cb0", "Neutral"

    ax.scatter([rsi.index[-1]], [latest], color=dot_color, zorder=5, s=30)
    ax.annotate(
        f"{latest:.1f} ({zone})",
        xy=(rsi.index[-1], latest),
        xytext=(-10, 12),
        textcoords="offset points",
        ha="right",
        fontsize=9,
        fontweight="bold",
        color=dot_color,
    )

    ax.legend(loc="upper left", fontsize=8, ncol=3, framealpha=0.85)
    ax.grid(True, alpha=0.3)


def plot_price_with_drawdown(ax, close: pd.Series, ticker: str) -> None:
    """Render price, the all-time-high envelope and the drawdown from the ATH."""
    if close.empty:
        ax.set_title(f"{ticker} — Price", fontweight="bold", fontsize=12)
        ax.text(
            0.5,
            0.5,
            "No data available",
            ha="center",
            va="center",
            transform=ax.transAxes,
            color="#a0aec0",
        )
        return

    ath = close.cummax()
    current = float(close.iloc[-1])
    peak = float(close.max())
    peak_date = close.idxmax()
    drawdown_pct = (current - peak) / peak * 100.0 if peak else 0.0

    ax.plot(close.index, close.values, color="#1a202c", linewidth=1.3, label="Close")
    ax.plot(ath.index, ath.values, color="#dd6b20", linestyle="--", linewidth=1.1, label="All-time high")

    # Shade the "underwater" area between price and its running peak.
    ax.fill_between(
        close.index,
        close.values,
        ath.values,
        where=(close.values < ath.values),
        color="#e53e3e",
        alpha=0.12,
        label="Drawdown (underwater)",
    )

    # Mark the all-time-high point and the latest close.
    ax.scatter([peak_date], [peak], color="#dd6b20", zorder=5, s=28)
    is_down = current < peak
    last_color = "#c53030" if is_down else "#2f855a"
    ax.scatter([close.index[-1]], [current], color=last_color, zorder=5, s=30)

    if is_down:
        # Show the drop from the all-time high at the right edge.
        ax.annotate(
            "",
            xy=(close.index[-1], current),
            xytext=(close.index[-1], peak),
            arrowprops=dict(arrowstyle="<->", color="#c53030", lw=1.2),
        )
        summary = (
            f"▼ Down {abs(drawdown_pct):.2f}% from all-time high\n"
            f"All-time high: ${peak:,.2f} ({peak_date:%Y-%m-%d})\n"
            f"Current: ${current:,.2f}"
        )
        box_color = "#fff5f5"
        edge_color = "#c53030"
    else:
        summary = f"▲ At all-time high\nCurrent: ${current:,.2f}"
        box_color = "#f0fff4"
        edge_color = "#2f855a"

    ax.text(
        0.012,
        0.04,
        summary,
        transform=ax.transAxes,
        fontsize=9,
        fontweight="bold",
        va="bottom",
        ha="left",
        color=edge_color,
        bbox=dict(boxstyle="round,pad=0.4", facecolor=box_color, edgecolor=edge_color, alpha=0.95),
    )

    dd_label = f"Down {abs(drawdown_pct):.2f}% from ATH" if is_down else "At all-time high"
    ax.set_title(f"{ticker} — Price  ·  {dd_label}", fontweight="bold", fontsize=12)
    ax.set_ylabel("Price ($)")
    ax.legend(loc="upper left", fontsize=8, framealpha=0.85)
    ax.grid(True, alpha=0.3)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    ticker = (args[0] if args else DEFAULT_TICKER).upper()

    print(f"Fetching data for {ticker} ...")
    close_price, src_price = get_close_series(ticker, **PRICE_HISTORY)
    close_4h, src_4h = get_close_series(ticker, **FOUR_HOUR)
    close_weekly, src_weekly = get_close_series(ticker, **WEEKLY)

    rsi_4h = compute_rsi(close_4h)
    rsi_weekly = compute_rsi(close_weekly)

    if close_price.empty and rsi_4h.empty and rsi_weekly.empty:
        print(
            f"No data returned for '{ticker}' (live + cache). "
            "Yahoo may be rate-limiting; try again later or check the symbol."
        )
        return 1

    used_cache = "cache" in (src_price, src_4h, src_weekly)
    if used_cache:
        print("  note: using on-disk cache fallback (live data unavailable).")

    fig, (ax_price, ax_4h, ax_weekly) = plt.subplots(
        3, 1, figsize=(13, 13), gridspec_kw={"hspace": 0.35}
    )
    suptitle = f"{ticker} — Price, Drawdown & RSI"
    if used_cache:
        suptitle += "  (offline cache)"
    fig.suptitle(suptitle, fontsize=15, fontweight="bold")

    plot_price_with_drawdown(ax_price, close_price, ticker)
    plot_rsi(ax_4h, rsi_4h, f"{ticker} — 4-Hour RSI ({RSI_PERIOD})")
    plot_rsi(ax_weekly, rsi_weekly, f"{ticker} — Weekly RSI ({RSI_PERIOD})")

    # Tidy date axes.
    for ax in (ax_price, ax_4h, ax_weekly):
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        for label in ax.get_xticklabels():
            label.set_rotation(30)
            label.set_horizontalalignment("right")

    out_path = Path(__file__).resolve().parent / f"{ticker}_rsi_drawdown.png"
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    print(f"Saved chart to {out_path}")

    if SHOW:
        plt.show()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
