"""
Pydantic schemas for market data
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class StockBase(BaseModel):
    """Base stock schema"""
    symbol: str = Field(..., min_length=1, max_length=10)
    name: Optional[str] = None
    etf_type: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None


class StockCreate(StockBase):
    """Schema for creating a stock"""
    pass


class StockResponse(StockBase):
    """Schema for stock response"""
    id: int
    last_updated: datetime
    
    class Config:
        from_attributes = True


class CandleBase(BaseModel):
    """Base candle schema"""
    timestamp: datetime
    interval: str = "1d"
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None


class CandleCreate(CandleBase):
    """Schema for creating a candle"""
    pass


class CandleResponse(CandleBase):
    """Schema for candle response"""
    id: int
    stock_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class IndicatorBase(BaseModel):
    """Base indicator schema"""
    indicator_name: str
    value: float
    value2: Optional[float] = None
    value3: Optional[float] = None


class IndicatorResponse(IndicatorBase):
    """Schema for indicator response"""
    id: int
    candle_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class WatchlistBase(BaseModel):
    """Base watchlist schema"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_default: bool = False


class WatchlistCreate(WatchlistBase):
    """Schema for creating a watchlist"""
    pass


class WatchlistResponse(WatchlistBase):
    """Schema for watchlist response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WatchlistWithItems(WatchlistResponse):
    """Watchlist with items"""
    items: List['WatchlistItemResponse'] = []


class WatchlistItemBase(BaseModel):
    """Base watchlist item schema"""
    stock_id: int


class WatchlistItemCreate(WatchlistItemBase):
    """Schema for creating watchlist item"""
    pass


class WatchlistItemResponse(WatchlistItemBase):
    """Schema for watchlist item response"""
    id: int
    stock: Optional[StockResponse] = None
    added_at: datetime
    
    class Config:
        from_attributes = True


class TradeBase(BaseModel):
    """Base trade schema"""
    entry_price: float
    quantity: float
    entry_time: datetime
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: Optional[str] = None


class TradeCreate(TradeBase):
    """Schema for creating a trade"""
    stock_id: int


class TradeResponse(TradeBase):
    """Schema for trade response"""
    id: int
    stock_id: int
    is_open: bool
    is_winning: Optional[bool] = None
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    gross_pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SignalBase(BaseModel):
    """Base signal schema"""
    signal_type: str  # BUY, SELL, HOLD
    strength: float = Field(..., ge=0, le=100)
    reason: Optional[str] = None
    suggested_entry: Optional[float] = None
    suggested_stop_loss: Optional[float] = None
    suggested_take_profit: Optional[float] = None


class SignalCreate(SignalBase):
    """Schema for creating a signal"""
    stock_id: int


class SignalResponse(SignalBase):
    """Schema for signal response"""
    id: int
    stock_id: int
    is_active: bool
    acted_upon: bool
    generated_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class PriceDataResponse(BaseModel):
    """Current price data response"""
    symbol: str
    current_price: float
    previous_close: Optional[float] = None
    timestamp: datetime


class HistoricalDataRequest(BaseModel):
    """Request for historical data"""
    ticker: str
    period: str = "1y"
    interval: str = "1d"


class CandleResponseList(BaseModel):
    """List of candles response"""
    symbol: str
    interval: str
    candles: List[CandleResponse]
    count: int


# Update forward references
WatchlistWithItems.model_rebuild()
