#!/usr/bin/env python3
"""
Initialize VIX historical data from CBOE and save it to local cache.
This cache is used to calculate VIX change versus the previous close.
"""
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_vix_history_from_cboe() -> pd.DataFrame:
    """Download full VIX daily history from CBOE and keep the last 2 years."""
    url = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
    raw = pd.read_csv(url)
    if raw.empty:
        raise ValueError("CBOE VIX history CSV is empty")

    raw["DATE"] = pd.to_datetime(raw["DATE"], format="%m/%d/%Y", errors="coerce")
    raw = raw.dropna(subset=["DATE", "CLOSE"]).sort_values("DATE")

    cutoff = datetime.now() - timedelta(days=2 * 365)
    recent = raw[raw["DATE"] >= cutoff].copy()
    if recent.empty:
        raise ValueError("No VIX history rows found for the last 2 years")

    recent = recent.rename(
        columns={
            "DATE": "date",
            "OPEN": "open",
            "HIGH": "high",
            "LOW": "low",
            "CLOSE": "close",
        }
    )
    recent["volume"] = 0
    recent = recent[["date", "open", "high", "low", "close", "volume"]]
    recent = recent.set_index("date")
    return recent


def init_vix_history():
    """Download 2 years of VIX data and save to cache."""
    cache_dir = Path("backend/data/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    vix_cache_path = cache_dir / "IDX_VIX_1d.csv"
    
    try:
        logger.info("📥 Downloading 2 years of real VIX history from CBOE...")
        vix_data = download_vix_history_from_cboe()
    except Exception as e:
        logger.error(f"❌ Error downloading VIX history from CBOE: {e}")
        return False
    
    # Save to cache
    vix_data.to_csv(vix_cache_path)
    logger.info(f"✅ VIX history saved to {vix_cache_path}")
    logger.info(f"   Date range: {vix_data.index[0].date()} to {vix_data.index[-1].date()}")
    logger.info(f"   Records: {len(vix_data)}")
    
    # Show latest few records
    logger.info("\nLatest VIX data:")
    print(vix_data.tail(5).to_string())
    
    return True


if __name__ == "__main__":
    success = init_vix_history()
    exit(0 if success else 1)
