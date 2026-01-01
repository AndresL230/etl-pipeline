from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class StockPrice(BaseModel):
    """Stock price data model."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    daily_return: Optional[float] = None
    sma_7: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None

    class Config:
        from_attributes = True


class StockPriceAdvanced(StockPrice):
    """Stock price with advanced technical indicators."""
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    rsi: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    volatility_20: Optional[float] = None


class PriceQuery(BaseModel):
    """Query parameters for stock prices."""
    symbols: Optional[List[str]] = Field(None, description="Filter by symbols")
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of results")


class IndicatorQuery(BaseModel):
    """Query parameters for technical indicators."""
    symbol: str = Field(..., description="Stock symbol")
    indicator: str = Field(..., description="Indicator type (sma, ema, rsi, macd, bollinger)")
    window: Optional[int] = Field(None, description="Window size for indicator")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SymbolSummary(BaseModel):
    """Summary statistics for a symbol."""
    symbol: str
    latest_price: float
    latest_timestamp: datetime
    daily_return: Optional[float]
    avg_volume: float
    volatility: Optional[float]
    rsi: Optional[float] = Field(None, description="Latest RSI value")
    price_change_7d: Optional[float] = Field(None, description="7-day price change percentage")
    price_change_30d: Optional[float] = Field(None, description="30-day price change percentage")


class HealthCheck(BaseModel):
    """API health check response."""
    status: str
    timestamp: datetime
    database_connected: bool
    version: str = "1.0.0"
