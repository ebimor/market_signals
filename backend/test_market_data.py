"""
Test script to validate market data collector
"""
from market_data.data_fetcher import get_fetcher
from market_data.ticker_lists import (
    get_default_watchlist,
    get_market_health_tickers,
)


def test_single_ticker():
    """Test fetching data for a single ticker"""
    print("\n=== Testing Single Ticker ===")
    fetcher = get_fetcher()
    
    ticker = "AAPL"
    price = fetcher.get_current_price(ticker)
    print(f"Current price of {ticker}: ${price}")
    
    # Get historical data
    data = fetcher.get_historical_data(ticker, period="1mo", interval="1d")
    if data is not None:
        print(f"Historical data shape: {data.shape}")
        print("\nLast 5 days:")
        print(data.tail())
    
    # Get ticker info
    info = fetcher.get_ticker_info(ticker)
    print(f"\nTicker info: {info}")


def test_canadian_etf():
    """Test fetching data for Canadian ETF"""
    print("\n=== Testing Canadian ETF ===")
    fetcher = get_fetcher()
    
    ticker = "VFV"  # Vanguard US Index ETF
    price = fetcher.get_current_price(ticker)
    print(f"Current price of {ticker}: ${price}")
    
    # Get intraday data
    data = fetcher.get_intraday_data(ticker, interval="5m", days=5)
    if data is not None:
        print(f"Intraday data shape: {data.shape}")
        print("\nLast 5 candles:")
        print(data.tail())


def test_default_watchlist():
    """Test fetching data for default watchlist"""
    print("\n=== Testing Default Watchlist ===")
    fetcher = get_fetcher()
    
    watchlist = get_default_watchlist()
    print(f"Default watchlist: {watchlist}")
    
    prices = {}
    for ticker in watchlist:
        price = fetcher.get_current_price(ticker)
        prices[ticker] = price
        print(f"  {ticker}: ${price}")


def test_market_health():
    """Test market health indicators"""
    print("\n=== Testing Market Health ===")
    fetcher = get_fetcher()
    
    health_tickers = get_market_health_tickers()
    print(f"Market health tickers: {health_tickers}")
    
    prices = {}
    for ticker in health_tickers:
        price = fetcher.get_current_price(ticker)
        prices[ticker] = price
        print(f"  {ticker}: {price}")
    
    vix = prices.get("^VIX")
    spy = prices.get("^GSPC")
    print(f"\nMarket Assessment:")
    print(f"  S&P 500: {spy}")
    print(f"  VIX: {vix}")
    
    if vix and vix > 30:
        print("  STATUS: HIGH VOLATILITY - NEW TRADES DISABLED")
    elif vix and vix > 20:
        print("  STATUS: MEDIUM VOLATILITY - CAUTIOUS")
    else:
        print("  STATUS: LOW VOLATILITY - OK FOR TRADING")


def test_cache():
    """Test caching functionality"""
    print("\n=== Testing Cache ===")
    fetcher = get_fetcher()
    
    # First fetch
    print("First fetch of AAPL...")
    price1 = fetcher.get_current_price("AAPL")
    print(f"Price: {price1}")
    print(f"Cache stats: {fetcher.get_cache_stats()}")
    
    # Second fetch (should use cache)
    print("\nSecond fetch of AAPL (should be cached)...")
    price2 = fetcher.get_current_price("AAPL")
    print(f"Price: {price2}")
    print(f"Cache stats: {fetcher.get_cache_stats()}")
    
    # Clear cache
    fetcher.clear_cache()
    print("\nCache cleared")
    print(f"Cache stats: {fetcher.get_cache_stats()}")


if __name__ == "__main__":
    print("SafeSwing Trader - Market Data Collector Tests")
    print("=" * 50)
    
    test_single_ticker()
    test_canadian_etf()
    test_default_watchlist()
    test_market_health()
    test_cache()
    
    print("\n" + "=" * 50)
    print("Tests completed!")
