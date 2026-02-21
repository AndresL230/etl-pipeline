from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
import logging

from src.config.settings import Config
from src.api.models import (
    StockPrice,
    StockPriceAdvanced,
    PriceQuery,
    IndicatorQuery,
    SymbolSummary,
    HealthCheck
)
from src.transformers.financial_metrics import (
    add_sma,
    add_ema,
    compute_rsi,
    add_bollinger_bands,
    compute_macd,
    add_volatility
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stock ETL API",
    description="REST API for stock price data and technical indicators",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db_engine():
    """Dependency to get database engine."""
    config = Config()
    try:
        engine = create_engine(config.DATABASE_URL())
        return engine
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Stock ETL API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check(engine=Depends(get_db_engine)):
    """Health check endpoint."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    return HealthCheck(
        status="healthy" if db_connected else "degraded",
        timestamp=datetime.now(),
        database_connected=db_connected
    )


@app.get("/api/v1/prices", response_model=List[StockPrice], tags=["Prices"])
async def get_prices(
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols"),
    start_date: Optional[datetime] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[datetime] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Max results"),
    engine=Depends(get_db_engine)
):
    """Get stock prices with basic technical indicators."""
    try:
        query = "SELECT * FROM stock_prices WHERE 1=1"
        params = {}

        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
            placeholders = ','.join([f':symbol{i}' for i in range(len(symbol_list))])
            query += f" AND symbol IN ({placeholders})"
            for i, symbol in enumerate(symbol_list):
                params[f'symbol{i}'] = symbol

        if start_date:
            query += " AND timestamp >= :start_date"
            params['start_date'] = start_date

        if end_date:
            query += " AND timestamp <= :end_date"
            params['end_date'] = end_date

        query += " ORDER BY timestamp DESC LIMIT :limit"
        params['limit'] = limit

        df = pd.read_sql(text(query), engine, params=params)

        if df.empty:
            return []

        # Convert to list of dicts
        return df.to_dict('records')

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")


@app.get("/api/v1/prices/advanced", response_model=List[StockPriceAdvanced], tags=["Prices"])
async def get_prices_advanced(
    symbols: Optional[str] = Query(None, description="Comma-separated list of symbols"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(100, ge=1, le=1000),
    engine=Depends(get_db_engine)
):
    """Get stock prices with all advanced technical indicators computed on-the-fly."""
    try:
        query = "SELECT * FROM stock_prices WHERE 1=1"
        params = {}

        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
            placeholders = ','.join([f':symbol{i}' for i in range(len(symbol_list))])
            query += f" AND symbol IN ({placeholders})"
            for i, symbol in enumerate(symbol_list):
                params[f'symbol{i}'] = symbol

        if start_date:
            query += " AND timestamp >= :start_date"
            params['start_date'] = start_date

        if end_date:
            query += " AND timestamp <= :end_date"
            params['end_date'] = end_date

        query += " ORDER BY symbol, timestamp"

        df = pd.read_sql(text(query), engine, params=params)

        if df.empty:
            return []

        # Compute advanced indicators
        df = add_ema(df, window=12)
        df = add_ema(df, window=26)
        df = compute_rsi(df, window=14)
        df = add_bollinger_bands(df, window=20)
        df = compute_macd(df)
        df = add_volatility(df, window=20)

        # Sort by timestamp and apply limit
        df = df.sort_values('timestamp', ascending=False).head(limit)

        return df.to_dict('records')

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")


@app.get("/api/v1/symbols", response_model=List[str], tags=["Symbols"])
async def get_symbols(engine=Depends(get_db_engine)):
    """Get list of all available symbols."""
    try:
        query = "SELECT DISTINCT symbol FROM stock_prices ORDER BY symbol"
        df = pd.read_sql(text(query), engine)
        return df['symbol'].tolist()

    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database query failed")


@app.get("/api/v1/symbols/{symbol}/summary", response_model=SymbolSummary, tags=["Symbols"])
async def get_symbol_summary(symbol: str, engine=Depends(get_db_engine)):
    """Get summary statistics for a specific symbol."""
    try:
        symbol = symbol.upper()

        # Get latest price
        query_latest = """
            SELECT * FROM stock_prices
            WHERE symbol = :symbol
            ORDER BY timestamp DESC
            LIMIT 1
        """
        latest = pd.read_sql(text(query_latest), engine, params={'symbol': symbol})

        if latest.empty:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")

        # Get historical data for calculations
        query_hist = """
            SELECT * FROM stock_prices
            WHERE symbol = :symbol
            ORDER BY timestamp DESC
            LIMIT 50
        """
        df = pd.read_sql(text(query_hist), engine, params={'symbol': symbol})

        # Calculate statistics
        df = df.sort_values('timestamp')
        df = compute_rsi(df)

        latest_row = df.iloc[-1]
        avg_volume = df['volume'].mean()

        # Price changes
        price_7d = df.iloc[-7]['close'] if len(df) >= 7 else None
        price_30d = df.iloc[0]['close'] if len(df) >= 30 else None
        current_price = latest_row['close']

        price_change_7d = ((current_price - price_7d) / price_7d * 100) if price_7d else None
        price_change_30d = ((current_price - price_30d) / price_30d * 100) if price_30d else None

        # Volatility
        returns = df['close'].pct_change()
        volatility = returns.std() if len(returns) > 1 else None

        return SymbolSummary(
            symbol=symbol,
            latest_price=current_price,
            latest_timestamp=latest_row['timestamp'],
            daily_return=latest_row.get('daily_return'),
            avg_volume=avg_volume,
            volatility=volatility,
            rsi=latest_row.get('rsi'),
            price_change_7d=price_change_7d,
            price_change_30d=price_change_30d
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting summary for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/indicators/{symbol}/{indicator}", tags=["Indicators"])
async def get_indicator(
    symbol: str,
    indicator: str,
    window: Optional[int] = Query(None, description="Window size (for SMA/EMA)"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000),
    engine=Depends(get_db_engine)
):
    """Get specific technical indicator for a symbol.

    Available indicators: sma, ema, rsi, macd, bollinger, volatility
    """
    try:
        symbol = symbol.upper()
        indicator = indicator.lower()

        # Fetch data
        query = "SELECT * FROM stock_prices WHERE symbol = :symbol"
        params = {'symbol': symbol}

        if start_date:
            query += " AND timestamp >= :start_date"
            params['start_date'] = start_date

        if end_date:
            query += " AND timestamp <= :end_date"
            params['end_date'] = end_date

        query += " ORDER BY timestamp"

        df = pd.read_sql(text(query), engine, params=params)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")

        # Compute indicator
        if indicator == 'sma':
            window = window or 20
            df = add_sma(df, window=window)
            result_cols = ['timestamp', f'sma_{window}']

        elif indicator == 'ema':
            window = window or 12
            df = add_ema(df, window=window)
            result_cols = ['timestamp', f'ema_{window}']

        elif indicator == 'rsi':
            df = compute_rsi(df, window=window or 14)
            result_cols = ['timestamp', 'rsi']

        elif indicator == 'macd':
            df = compute_macd(df)
            result_cols = ['timestamp', 'macd', 'macd_signal', 'macd_histogram']

        elif indicator == 'bollinger':
            df = add_bollinger_bands(df, window=window or 20)
            result_cols = ['timestamp', 'bb_upper', 'bb_middle', 'bb_lower']

        elif indicator == 'volatility':
            df = add_volatility(df, window=window or 20)
            result_cols = ['timestamp', f'volatility_{window or 20}']

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown indicator: {indicator}. Available: sma, ema, rsi, macd, bollinger, volatility"
            )

        # Return limited results
        df = df[result_cols].tail(limit)
        return df.to_dict('records')

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error computing {indicator} for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
