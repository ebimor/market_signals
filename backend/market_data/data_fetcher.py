"""
Market data fetcher using Yahoo Finance
Provides free, real-time market data for US stocks and Canadian ETFs
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MarketDataFetcher:
    """Fetches market data from Yahoo Finance with caching"""
    
    def __init__(self, cache_ttl_minutes: int = 5):
        """
        Initialize the market data fetcher
        
        Args:
            cache_ttl_minutes: Cache time-to-live in minutes
        """
        self.cache_ttl_minutes = cache_ttl_minutes
        self._cache: Dict[str, Tuple[pd.DataFrame, datetime]] = {}
        self.cache_dir = Path("backend/data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_file_path(self, ticker: str, interval: str = "1d") -> Path:
        safe_ticker = ticker.upper().replace("^", "IDX_")
        return self.cache_dir / f"{safe_ticker}_{interval}.csv"

    def _save_disk_cache(self, ticker: str, interval: str, data: pd.DataFrame) -> None:
        """Persist historical data to disk as fallback when yfinance is unavailable."""
        try:
            path = self._cache_file_path(ticker, interval)
            to_save = data.copy()
            to_save.to_csv(path)
        except Exception as e:
            logger.warning(f"Could not save cache for {ticker} ({interval}): {e}")

    def _load_disk_cache(self, ticker: str, interval: str) -> Optional[pd.DataFrame]:
        """Load cached data from disk (if available)."""
        path = self._cache_file_path(ticker, interval)
        safe_ticker = ticker.upper().replace("^", "IDX_")
        legacy_path = self.cache_dir / f"{safe_ticker}.csv"
        candidate_paths = [path, legacy_path]

        for p in candidate_paths:
            if not p.exists():
                continue
            try:
                data = pd.read_csv(p, index_col=0, parse_dates=True)
                data.columns = [str(col).lower() for col in data.columns]
                if not data.empty:
                    return data
            except Exception as e:
                logger.warning(f"Could not load cache file {p.name} for {ticker} ({interval}): {e}")

        return None
    
    def _is_cache_valid(self, cache_time: datetime) -> bool:
        """Check if cached data is still valid"""
        return datetime.now() - cache_time < timedelta(minutes=self.cache_ttl_minutes)
    
    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get current price for a ticker
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Current price or None if failed
        """
        try:
            data = yf.Ticker(ticker)
            info = data.history(period="1d")
            if not info.empty:
                return float(info["Close"].iloc[-1])
        except Exception as e:
            logger.error(f"Error fetching price for {ticker}: {e}")

        # Fallback to latest close from cached historical data
        historical = self.get_historical_data(ticker, period="1mo", interval="1d", use_cache=True)
        if historical is not None and not historical.empty and "close" in historical.columns:
            try:
                return float(historical["close"].iloc[-1])
            except Exception:
                pass
        return None
    
    def get_historical_data(
        self,
        ticker: str,
        period: str = "1y",
        interval: str = "1d",
        use_cache: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        Get historical market data (OHLCV)
        
        Args:
            ticker: Stock ticker symbol
            period: Data period (e.g., "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
            interval: Data interval (e.g., "1m", "5m", "15m", "30m", "60m", "1d", "1wk", "1mo")
            use_cache: Whether to use cached data if available
            
        Returns:
            DataFrame with OHLCV data or None if failed
        """
        ticker = ticker.upper()
        cache_key = f"{ticker}_{period}_{interval}"
        
        # Check cache
        if use_cache and cache_key in self._cache:
            data, cache_time = self._cache[cache_key]
            if self._is_cache_valid(cache_time):
                logger.debug(f"Using cached data for {ticker}")
                return data.copy()
        
        try:
            logger.info(f"Fetching {period} data for {ticker} at {interval} interval")
            data = yf.download(
                ticker,
                period=period,
                interval=interval,
                progress=False,
                threads=False,
                auto_adjust=False,
            )
            
            if data.empty:
                logger.warning(f"No live data returned for {ticker}; trying local cache")
                disk_data = self._load_disk_cache(ticker, interval)
                if disk_data is not None:
                    self._cache[cache_key] = (disk_data.copy(), datetime.now())
                    return disk_data
                return None
            
            # Rename columns to lowercase
            data.columns = [col.lower() for col in data.columns]
            
            # Cache the data
            self._cache[cache_key] = (data.copy(), datetime.now())
            self._save_disk_cache(ticker, interval, data)
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {ticker}: {e}")
            disk_data = self._load_disk_cache(ticker, interval)
            if disk_data is not None:
                logger.info(f"Using local historical cache for {ticker} ({interval})")
                self._cache[cache_key] = (disk_data.copy(), datetime.now())
                return disk_data
            return None
    
    def get_intraday_data(
        self,
        ticker: str,
        interval: str = "5m",
        days: int = 5
    ) -> Optional[pd.DataFrame]:
        """
        Get intraday market data
        
        Args:
            ticker: Stock ticker symbol
            interval: Data interval ("1m", "5m", "15m", "30m", "60m")
            days: Number of days of historical data
            
        Returns:
            DataFrame with intraday OHLCV data
        """
        cache_key = f"{ticker}_intraday_{interval}_{days}d"
        
        # Check cache (shorter TTL for intraday)
        if cache_key in self._cache:
            data, cache_time = self._cache[cache_key]
            if datetime.now() - cache_time < timedelta(minutes=1):
                logger.debug(f"Using cached intraday data for {ticker}")
                return data.copy()
        
        try:
            period_map = {
                1: "1d",
                5: "5d",
                7: "7d",
                30: "1mo",
                60: "2mo",
            }
            period = period_map.get(days, "5d")
            
            logger.info(f"Fetching intraday {interval} data for {ticker}")
            data = yf.download(
                ticker,
                period=period,
                interval=interval,
                progress=False
            )
            
            if data.empty:
                logger.warning(f"No intraday data returned for {ticker}")
                return None
            
            # Rename columns to lowercase
            data.columns = [col.lower() for col in data.columns]
            
            # Cache the data
            self._cache[cache_key] = (data.copy(), datetime.now())
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching intraday data for {ticker}: {e}")
            return None
    
    def get_multiple_tickers(
        self,
        tickers: List[str],
        period: str = "1d",
        interval: str = "1d"
    ) -> Dict[str, Optional[pd.DataFrame]]:
        """
        Get historical data for multiple tickers
        
        Args:
            tickers: List of ticker symbols
            period: Data period
            interval: Data interval
            
        Returns:
            Dictionary mapping ticker to DataFrame
        """
        try:
            logger.info(f"Fetching data for {len(tickers)} tickers")
            data = yf.download(
                " ".join(tickers),
                period=period,
                interval=interval,
                progress=False
            )
            
            if data.empty:
                logger.warning("No data returned for tickers")
                return {ticker: None for ticker in tickers}
            
            result = {}
            for ticker in tickers:
                try:
                    if len(tickers) == 1:
                        ticker_data = data.copy()
                    else:
                        ticker_data = data[[col for col in data.columns if col[1] == ticker]] if len(data.columns[0]) > 1 else data
                    
                    ticker_data.columns = [col.lower() for col in ticker_data.columns]
                    result[ticker] = ticker_data if not ticker_data.empty else None
                except Exception as e:
                    logger.error(f"Error processing data for {ticker}: {e}")
                    result[ticker] = None
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching multiple tickers: {e}")
            return {ticker: None for ticker in tickers}
    
    def get_ticker_info(self, ticker: str) -> Optional[Dict]:
        """
        Get basic ticker information
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with ticker info or None
        """
        try:
            info = yf.Ticker(ticker).info
            return {
                "symbol": ticker,
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap", None),
                "pe_ratio": info.get("trailingPE", None),
                "dividend_yield": info.get("dividendYield", None),
                "52_week_high": info.get("fiftyTwoWeekHigh", None),
                "52_week_low": info.get("fiftyTwoWeekLow", None),
            }
        except Exception as e:
            logger.error(f"Error fetching info for {ticker}: {e}")
            return None
    
    def clear_cache(self):
        """Clear all cached data"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        total_size = len(self._cache)
        valid_size = sum(
            1 for _, (_, cache_time) in self._cache.items()
            if self._is_cache_valid(cache_time)
        )
        return {
            "total_cached": total_size,
            "valid_cached": valid_size,
            "expired_cached": total_size - valid_size,
        }


# Global instance
_fetcher: Optional[MarketDataFetcher] = None


def get_fetcher() -> MarketDataFetcher:
    """Get or create global fetcher instance"""
    global _fetcher
    if _fetcher is None:
        _fetcher = MarketDataFetcher()
    return _fetcher
