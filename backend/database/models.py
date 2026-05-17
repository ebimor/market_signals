"""
SQLAlchemy models for SafeSwing Trader
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Stock(Base):
    """Stock/ETF master data"""
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(String(255))
    etf_type = Column(String(50))  # e.g., "US_STOCK", "BMO_ETF", "ISHARES_ETF", "VANGUARD_ETF"
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candles = relationship("Candle", back_populates="stock", cascade="all, delete-orphan")
    watchlist_items = relationship("WatchlistItem", back_populates="stock", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="stock", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Stock {self.symbol}>"


class Candle(Base):
    """OHLCV candlestick data"""
    __tablename__ = "candles"
    __table_args__ = (
        UniqueConstraint("stock_id", "timestamp", "interval", name="uq_stock_time_interval"),
        Index("ix_stock_timestamp", "stock_id", "timestamp"),
        Index("ix_interval", "interval"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    interval = Column(String(10), default="1d")  # "1m", "5m", "15m", "30m", "60m", "1d", "1wk", "1mo"
    
    # OHLCV data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer)
    
    # Calculated fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="candles")
    indicators = relationship("Indicator", back_populates="candle", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Candle {self.stock_id} {self.timestamp} {self.interval}>"


class Indicator(Base):
    """Technical indicators"""
    __tablename__ = "indicators"
    __table_args__ = (
        Index("ix_candle_indicator", "candle_id", "indicator_name"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    candle_id = Column(Integer, ForeignKey("candles.id"), nullable=False)
    indicator_name = Column(String(50), nullable=False)  # "RSI", "MACD", "EMA", "SMA", "ATR", etc.
    value = Column(Float)
    
    # Optional fields for multi-value indicators
    value2 = Column(Float, nullable=True)  # e.g., MACD signal
    value3 = Column(Float, nullable=True)  # e.g., MACD histogram
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    candle = relationship("Candle", back_populates="indicators")
    
    def __repr__(self):
        return f"<Indicator {self.indicator_name} {self.value}>"


class Watchlist(Base):
    """User watchlists"""
    __tablename__ = "watchlists"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    is_default = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = relationship("WatchlistItem", back_populates="watchlist", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Watchlist {self.name}>"


class WatchlistItem(Base):
    """Items in a watchlist"""
    __tablename__ = "watchlist_items"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "stock_id", name="uq_watchlist_stock"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=False)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    watchlist = relationship("Watchlist", back_populates="items")
    stock = relationship("Stock", back_populates="watchlist_items")
    
    def __repr__(self):
        return f"<WatchlistItem watchlist={self.watchlist_id} stock={self.stock_id}>"


class Trade(Base):
    """Recorded trades"""
    __tablename__ = "trades"
    __table_args__ = (
        Index("ix_stock_entry_time", "stock_id", "entry_time"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    
    # Entry details
    entry_time = Column(DateTime, nullable=False)
    entry_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    
    # Exit details
    exit_time = Column(DateTime, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_reason = Column(String(100))  # "TP", "SL", "Manual", "Error"
    
    # Risk management
    stop_loss = Column(Float)
    take_profit = Column(Float)
    atr_at_entry = Column(Float)  # ATR value at entry for reference
    
    # Status
    is_open = Column(Boolean, default=True)
    is_winning = Column(Boolean, nullable=True)  # True if profitable, False if loss, None if open
    
    # Calculated fields
    gross_pnl = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)
    holding_minutes = Column(Integer, nullable=True)
    
    notes = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock = relationship("Stock", back_populates="trades")
    
    def __repr__(self):
        return f"<Trade {self.stock_id} entry={self.entry_time}>"


class MarketHealth(Base):
    """Market health metrics snapshot"""
    __tablename__ = "market_health"
    __table_args__ = (
        Index("ix_timestamp", "timestamp"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Market indicators
    spy_price = Column(Float)
    spy_50_day_ma = Column(Float)
    vix_value = Column(Float)
    market_trend = Column(String(20))  # "BULLISH", "BEARISH", "NEUTRAL"
    
    # Assessment
    is_healthy = Column(Boolean)
    risk_level = Column(String(20))  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    notes = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MarketHealth {self.timestamp}>"


class Signal(Base):
    """Trading signals generated by the signal engine"""
    __tablename__ = "signals"
    __table_args__ = (
        Index("ix_stock_time", "stock_id", "generated_at"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    
    signal_type = Column(String(10), nullable=False)  # "BUY", "SELL", "HOLD"
    strength = Column(Float)  # 0-100, confidence score
    
    # Signal details
    generated_at = Column(DateTime, default=datetime.utcnow)
    reason = Column(String(500))  # Why the signal was generated
    
    # Suggested entry/exit
    suggested_entry = Column(Float)
    suggested_stop_loss = Column(Float)
    suggested_take_profit = Column(Float)
    
    # Status
    is_active = Column(Boolean, default=True)
    acted_upon = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Signal {self.signal_type} {self.stock_id}>"
