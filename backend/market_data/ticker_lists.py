"""
Ticker lists for SafeSwing Trader
US stocks and Canadian ETFs that are tradable in Canada
"""

# Popular US stocks tradable in Canada
US_STOCKS = [
    # Tech Giants
    "AAPL", "MSFT", "GOOGL", "GOOG", "NVDA", "TSLA", "META", "AMZN",
    # Financial
    "JPM", "BAC", "WFC", "GS", "C", "BLK", "Scheering",
    # Healthcare
    "UNH", "JNJ", "PFE", "ABBV", "LLY", "CVS", "ABT", "TMO",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC",
    # Industrials
    "BA", "GE", "CAT", "MMM", "HON", "ITW",
    # Consumer
    "WMT", "KO", "PEP", "MCD", "SBUX", "NKE", "TJX",
    # Utilities
    "NEE", "DUK", "SO", "D", "AEP", "WEC",
    # Real Estate
    "SPG", "ARE", "AVB", "PLD", "DLR",
    # Communication
    "VZ", "T", "CMCSA", "CHTR",
    # ETFs (US-listed)
    "SPY", "QQQ", "IWM", "DIA",  # Broad market
]

# Canadian ETFs - BMO
BMO_ETFS = [
    "ZSP",      # BMO S&P 500 Index ETF
    "ZUE",      # BMO US Equity Index ETF
    "ZCS",      # BMO Canadian Equity ETF
    "ZNQ",      # BMO NASDAQ 100 Index ETF
    "ZEB",      # BMO Emerging Markets Bond Index ETF
    "ZGD",      # BMO Global Diversified Growth ETF
]

# Canadian ETFs - iShares
ISHARES_ETFS = [
    "XUS",      # iShares Core U.S. Index ETF
    "XUU",      # iShares U.S. Index ETF
    "XUL",      # iShares U.S. Dividend Aristocrats ETF
    "XXT",      # iShares Growth ETF Portfolio
    "XCB",      # iShares Canadian Corporate Bond Index ETF
    "XGB",      # iShares Global Government Bond Index ETF
]

# Canadian ETFs - Vanguard
VANGUARD_ETFS = [
    "VFV",      # Vanguard US Index Index ETF
    "VSP",      # Vanguard US Total Market Index ETF
    "VUN",      # Vanguard U.S. Total Market Diversified Index ETF
    "VFV",      # Vanguard U.S. Index ETF
    "VRE",      # Vanguard Real Estate Index ETF
    "VAB",      # Vanguard Canadian Aggregate Bond Index ETF
]

# Canadian ETFs - RBC
RBC_ETFS = [
    "RFV",      # RBC U.S. Index ETF
    "RSP",      # RBC U.S. Index ETF (Unhedged)
    "RBC",      # RBC Canadian Equity ETF
]

# Canadian ETFs - Leveraged/Inverse
LEVERAGED_ETFS = [
    "ZQQ",      # 3x leveraged NASDAQ ETF
    "HQQ",      # 2x inverse NASDAQ ETF
]

# Canadian ETFs - Other
OTHER_CANADIAN_ETFS = [
    "XIC",      # iShares Global Tech ETF
    "XIT",      # iShares Global Tech ETF
    "XEN",      # iShares Energy Infrastructure ETF
    "XGD",      # iShares Global Diversified Growth ETF
]

# Combine all Canadian ETFs
CANADIAN_ETFS = BMO_ETFS + ISHARES_ETFS + VANGUARD_ETFS + RBC_ETFS + LEVERAGED_ETFS + OTHER_CANADIAN_ETFS

# All supported tickers
ALL_TICKERS = US_STOCKS + CANADIAN_ETFS

# Common index tickers for market health checks
INDEX_TICKERS = [
    "^GSPC",    # S&P 500
    "^IXIC",    # NASDAQ
    "^DJI",     # Dow Jones
    "^VIX",     # VIX (volatility index)
    "^FTSE",    # FTSE 100
    "^N225",    # Nikkei 225
]

# Canadian index tickers
CANADIAN_INDEX_TICKERS = [
    "^GSPTSE",  # S&P/TSX Composite
    "^CADUSD",  # CAD/USD
]

def get_market_health_tickers():
    """Return tickers needed for market health assessment"""
    return INDEX_TICKERS + CANADIAN_INDEX_TICKERS

def get_default_watchlist():
    """Return a balanced default watchlist"""
    return [
        # Popular US stocks
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN",
        # Popular Canadian ETFs
        "XUS", "VFV", "ZSP",
        # ETFs for diversification
        "SPY", "QQQ", "XIC",
    ]
