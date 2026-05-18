"""
Data Loader Module - Download and cache market data from yfinance

Features:
- Auto-download OHLCV data from yfinance
- Cache downloaded data as CSV
- Load from cache for subsequent runs
- Support for custom date ranges
"""

import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# Cache directory
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)


class DataLoader:
    """Download and manage historical market data from yfinance"""
    
    @staticmethod
    def get_cache_path(symbol: str) -> str:
        """Get the cache file path for a symbol"""
        return os.path.join(CACHE_DIR, f"{symbol.upper()}.csv")
    
    @staticmethod
    def _save_to_cache(symbol: str, df: pd.DataFrame) -> None:
        """Save dataframe to cache CSV"""
        path = DataLoader.get_cache_path(symbol)
        df.to_csv(path)
        logger.info(f"✅ Cached {symbol} data ({len(df)} rows) to {path}")
    
    @staticmethod
    def _load_from_cache(symbol: str) -> Optional[pd.DataFrame]:
        """Load dataframe from cache CSV"""
        path = DataLoader.get_cache_path(symbol)
        if os.path.exists(path):
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            logger.info(f"✅ Loaded {symbol} from cache ({len(df)} rows)")
            return df
        return None
    
    @staticmethod
    def download_data(
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        period: str = "1y",
        interval: str = "1d",
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Download market data from yfinance and cache it.
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL', 'TSLA')
            start_date: Start date for download (overrides period)
            end_date: End date for download (default: today)
            period: Period string ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max')
            interval: Data interval ('1m', '5m', '15m', '30m', '60m', '1d', '1wk', '1mo')
            use_cache: Load from cache if available
            force_refresh: Ignore cache and re-download
            
        Returns:
            DataFrame with OHLCV data (Open, High, Low, Close, Volume)
            
        Example:
            >>> loader = DataLoader()
            >>> aapl = loader.download_data('AAPL', period='1y')
            >>> print(aapl.head())
        """
        symbol_upper = symbol.upper()
        
        # Check cache first
        if use_cache and not force_refresh:
            cached = DataLoader._load_from_cache(symbol_upper)
            if cached is not None:
                return cached
        
        logger.info(f"📥 Downloading {symbol_upper}...")
        
        try:
            # Set default end date to today
            if end_date is None:
                end_date = datetime.now()
            
            # Download data with retry logic
            df = None
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if start_date:
                        df = yf.download(
                            symbol_upper,
                            start=start_date,
                            end=end_date,
                            interval=interval,
                            progress=False
                        )
                    else:
                        df = yf.download(
                            symbol_upper,
                            period=period,
                            interval=interval,
                            progress=False
                        )
                    
                    if not df.empty:
                        break
                    elif attempt < max_retries - 1:
                        logger.warning(f"Retry {attempt + 1}/{max_retries} for {symbol_upper}...")
                        import time
                        time.sleep(1)
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                        import time
                        time.sleep(1)
                    else:
                        raise
            
            if df is None or df.empty:
                raise ValueError(f"No data returned for {symbol_upper} after {max_retries} attempts")
            
            # Ensure required columns exist
            required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            # Keep only required columns
            df = df[required_cols]
            
            # Convert index to datetime if not already
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            logger.info(f"✅ Downloaded {len(df)} rows of {symbol_upper} data")
            logger.info(f"   Date range: {df.index.min().date()} to {df.index.max().date()}")
            
            # Cache the data
            DataLoader._save_to_cache(symbol_upper, df)
            
            return df
        
        except Exception as e:
            logger.error(f"❌ Error downloading {symbol_upper}: {e}")
            raise
    
    @staticmethod
    def download_multiple(
        symbols: list,
        period: str = "1y",
        use_cache: bool = True,
        force_refresh: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """
        Download data for multiple symbols.
        
        Args:
            symbols: List of tickers to download
            period: Period for all downloads
            use_cache: Use cached data if available
            force_refresh: Force re-download all
            
        Returns:
            Dictionary mapping symbol to DataFrame
            
        Example:
            >>> data = DataLoader.download_multiple(['AAPL', 'MSFT', 'TSLA'], period='6mo')
            >>> print(data['AAPL'].head())
        """
        result = {}
        for symbol in symbols:
            try:
                result[symbol.upper()] = DataLoader.download_data(
                    symbol,
                    period=period,
                    use_cache=use_cache,
                    force_refresh=force_refresh
                )
            except Exception as e:
                logger.warning(f"Failed to download {symbol}: {e}")
        
        return result
    
    @staticmethod
    def clear_cache(symbol: Optional[str] = None) -> None:
        """
        Clear cache for a symbol or all symbols.
        
        Args:
            symbol: Specific symbol to clear, or None to clear all
        """
        if symbol:
            path = DataLoader.get_cache_path(symbol)
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Cleared cache for {symbol}")
        else:
            for file in os.listdir(CACHE_DIR):
                os.remove(os.path.join(CACHE_DIR, file))
            logger.info("Cleared all cache files")
    
    @staticmethod
    def get_cached_symbols() -> list:
        """Get list of cached symbols"""
        symbols = []
        for file in os.listdir(CACHE_DIR):
            if file.endswith('.csv'):
                symbols.append(file[:-4])  # Remove .csv extension
        return sorted(symbols)
    
    @staticmethod
    def get_cache_info(symbol: str) -> Optional[Dict]:
        """Get information about cached data for a symbol"""
        path = DataLoader.get_cache_path(symbol)
        if not os.path.exists(path):
            return None
        
        try:
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            return {
                'symbol': symbol.upper(),
                'rows': len(df),
                'start_date': df.index.min().date(),
                'end_date': df.index.max().date(),
                'file_size_kb': os.path.getsize(path) / 1024,
                'cached_at': datetime.fromtimestamp(os.path.getmtime(path))
            }
        except Exception as e:
            logger.error(f"Error reading cache info: {e}")
            return None
