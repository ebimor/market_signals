"""
Configuration management for SafeSwing Trader
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    api_title: str = "SafeSwing Trader API"
    api_version: str = "0.1.0"
    api_host: str = "localhost"
    api_port: int = 8000
    debug: bool = True
    
    # Database
    database_url: str = "sqlite:///./safeswing.db"
    
    # Market Data
    market_data_refresh_interval: int = 60  # seconds
    
    # Risk Management
    default_account_risk_percent: float = 0.01  # 1%
    default_stop_loss_atr_multiplier: float = 1.5
    default_take_profit_ratio: float = 2.0
    
    # Signal Engine
    vix_threshold: float = 30.0
    
    # External APIs
    polygon_api_key: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    alpaca_api_key: Optional[str] = None
    alpaca_secret_key: Optional[str] = None
    alpaca_paper_trading: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
