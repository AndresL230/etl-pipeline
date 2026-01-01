# Stock ETL API Guide

## Overview

The Stock ETL API provides RESTful endpoints for accessing stock price data and technical indicators. Built with FastAPI, it offers automatic API documentation, data validation, and high performance.

## Quick Start

### Starting the API Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Start the server
python api_server.py

# Or with uvicorn directly
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

###Access Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health & Status

#### GET `/health`
Check API health and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T10:30:00",
  "database_connected": true,
  "version": "1.0.0"
}
```

---

### Stock Prices

#### GET `/api/v1/prices`
Get stock prices with basic technical indicators (SMA, daily returns).

**Query Parameters:**
- `symbols` (string, optional): Comma-separated list of symbols (e.g., "AAPL,GOOGL")
- `start_date` (datetime, optional): Start date (YYYY-MM-DD)
- `end_date` (datetime, optional): End date (YYYY-MM-DD)
- `limit` (integer, optional): Max results (1-1000, default: 100)

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/prices?symbols=AAPL&limit=10"
```

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "timestamp": "2025-01-01T00:00:00",
    "open": 150.25,
    "high": 152.00,
    "low": 149.50,
    "close": 151.75,
    "volume": 50000000,
    "daily_return": 0.012,
    "sma_7": 150.50,
    "sma_20": 149.80,
    "sma_50": 148.90
  }
]
```

#### GET `/api/v1/prices/advanced`
Get stock prices with ALL advanced technical indicators (RSI, MACD, Bollinger Bands, etc.).

**Query Parameters:** (Same as `/api/v1/prices`)

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/prices/advanced?symbols=AAPL&limit=5"
```

**Response Includes:**
- All basic indicators (SMA, daily returns)
- `ema_12`, `ema_26`: Exponential Moving Averages
- `rsi`: Relative Strength Index (0-100)
- `bb_upper`, `bb_middle`, `bb_lower`: Bollinger Bands
- `macd`, `macd_signal`, `macd_histogram`: MACD indicators
- `volatility_20`: Rolling 20-day volatility

---

### Symbols

#### GET `/api/v1/symbols`
Get list of all available stock symbols.

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/symbols"
```

**Response:**
```json
["AAPL", "GOOGL", "MSFT", "TSLA"]
```

#### GET `/api/v1/symbols/{symbol}/summary`
Get comprehensive summary statistics for a specific symbol.

**Path Parameters:**
- `symbol` (string, required): Stock symbol (e.g., "AAPL")

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/symbols/AAPL/summary"
```

**Response:**
```json
{
  "symbol": "AAPL",
  "latest_price": 151.75,
  "latest_timestamp": "2025-01-01T00:00:00",
  "daily_return": 0.012,
  "avg_volume": 48500000,
  "volatility": 0.025,
  "rsi": 65.5,
  "price_change_7d": 3.5,
  "price_change_30d": 8.2
}
```

---

### Technical Indicators

#### GET `/api/v1/indicators/{symbol}/{indicator}`
Get specific technical indicator for a symbol.

**Path Parameters:**
- `symbol` (string, required): Stock symbol
- `indicator` (string, required): Indicator type

**Available Indicators:**
- `sma`: Simple Moving Average
- `ema`: Exponential Moving Average
- `rsi`: Relative Strength Index
- `macd`: MACD (includes signal and histogram)
- `bollinger`: Bollinger Bands
- `volatility`: Rolling volatility

**Query Parameters:**
- `window` (integer, optional): Window size for SMA/EMA (default varies by indicator)
- `start_date` (datetime, optional): Start date
- `end_date` (datetime, optional): End date
- `limit` (integer, optional): Max results (1-1000, default: 100)

**Example: Get RSI**
```bash
curl "http://localhost:8000/api/v1/indicators/AAPL/rsi?limit=10"
```

**Response:**
```json
[
  {
    "timestamp": "2025-01-01T00:00:00",
    "rsi": 65.5
  },
  {
    "timestamp": "2024-12-31T00:00:00",
    "rsi": 62.3
  }
]
```

**Example: Get SMA with custom window**
```bash
curl "http://localhost:8000/api/v1/indicators/AAPL/sma?window=50&limit=20"
```

**Response:**
```json
[
  {
    "timestamp": "2025-01-01T00:00:00",
    "sma_50": 148.90
  }
]
```

**Example: Get MACD**
```bash
curl "http://localhost:8000/api/v1/indicators/AAPL/macd"
```

**Response:**
```json
[
  {
    "timestamp": "2025-01-01T00:00:00",
    "macd": 2.5,
    "macd_signal": 2.1,
    "macd_histogram": 0.4
  }
]
```

**Example: Get Bollinger Bands**
```bash
curl "http://localhost:8000/api/v1/indicators/AAPL/bollinger?window=20"
```

**Response:**
```json
[
  {
    "timestamp": "2025-01-01T00:00:00",
    "bb_upper": 155.50,
    "bb_middle": 150.00,
    "bb_lower": 144.50
  }
]
```

---

## Technical Indicator Explanations

### Simple Moving Average (SMA)
Average price over a specific window. Commonly used: 7, 20, 50, 200 days.
- **Use**: Identify trends and support/resistance levels
- **Signal**: Price above SMA = bullish, below = bearish

### Exponential Moving Average (EMA)
Weighted average giving more importance to recent prices.
- **Use**: Faster reaction to price changes than SMA
- **Common**: 12-day and 26-day for MACD calculation

### Relative Strength Index (RSI)
Momentum oscillator measuring speed and magnitude of price changes.
- **Range**: 0-100
- **Overbought**: RSI > 70
- **Oversold**: RSI < 30
- **Use**: Identify potential reversals

### Bollinger Bands
Volatility bands placed above and below a moving average.
- **Components**: Upper band, middle (SMA), lower band
- **Width**: ±2 standard deviations (default)
- **Use**: Volatility and breakout signals
  - Price touching upper band: potentially overbought
  - Price touching lower band: potentially oversold

### MACD (Moving Average Convergence Divergence)
Trend-following momentum indicator.
- **MACD Line**: 12-day EMA - 26-day EMA
- **Signal Line**: 9-day EMA of MACD line
- **Histogram**: MACD line - Signal line
- **Signals**:
  - MACD crosses above signal: bullish
  - MACD crosses below signal: bearish

### Volatility
Standard deviation of returns over a rolling window.
- **Higher values**: More volatile (risky)
- **Lower values**: More stable
- **Use**: Risk assessment, position sizing

---

## Python Client Examples

### Using `requests` library

```python
import requests
import pandas as pd

BASE_URL = "http://localhost:8000"

# Get prices
response = requests.get(f"{BASE_URL}/api/v1/prices", params={
    "symbols": "AAPL,GOOGL",
    "limit": 50
})
prices = response.json()
df = pd.DataFrame(prices)

# Get advanced indicators
response = requests.get(f"{BASE_URL}/api/v1/prices/advanced", params={
    "symbols": "AAPL",
    "limit": 100
})
advanced_data = pd.DataFrame(response.json())

# Get symbol summary
response = requests.get(f"{BASE_URL}/api/v1/symbols/AAPL/summary")
summary = response.json()
print(f"AAPL RSI: {summary['rsi']}")

# Get specific indicator
response = requests.get(f"{BASE_URL}/api/v1/indicators/AAPL/rsi", params={
    "limit": 30
})
rsi_data = pd.DataFrame(response.json())
```

### Using `httpx` (async)

```python
import httpx
import asyncio

async def get_stock_data():
    async with httpx.AsyncClient() as client:
        # Get multiple symbols
        symbols = ["AAPL", "GOOGL", "MSFT"]

        tasks = [
            client.get(f"http://localhost:8000/api/v1/symbols/{symbol}/summary")
            for symbol in symbols
        ]

        responses = await asyncio.gather(*tasks)

        for response in responses:
            data = response.json()
            print(f"{data['symbol']}: ${data['latest_price']:.2f} (RSI: {data['rsi']:.1f})")

# Run
asyncio.run(get_stock_data())
```

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "Symbol INVALID not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Unknown indicator: invalid. Available: sma, ema, rsi, macd, bollinger, volatility"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Database query failed"
}
```

---

## Performance Notes

- **Caching**: Not currently implemented (planned)
- **Rate Limiting**: Not currently implemented
- **Pagination**: Use `limit` parameter; max 1000 results per request
- **Advanced Indicators**: Computed on-the-fly; may be slower for large datasets

---

## Development & Testing

### Running Tests
```bash
source .venv/bin/activate
pytest tests/ -v
```

### Testing API Endpoints
```bash
# Using curl
curl -X GET "http://localhost:8000/api/v1/prices?symbols=AAPL&limit=5"

# Using httpie
http GET "http://localhost:8000/api/v1/prices?symbols=AAPL&limit=5"

# Using Python
python -c "import requests; print(requests.get('http://localhost:8000/health').json())"
```

---

## Future Enhancements

- [ ] WebSocket support for real-time price updates
- [ ] Authentication & API keys
- [ ] Rate limiting
- [ ] Redis caching for frequently accessed data
- [ ] Historical data export (CSV, Excel)
- [ ] Batch endpoint for multiple symbols
- [ ] Custom indicator calculations via POST
- [ ] GraphQL support

---

## Troubleshooting

### API won't start
- Ensure database is accessible
- Check that port 8000 is not in use
- Verify all dependencies are installed: `pip install -r requirements.txt`

### Database connection errors
- Verify DATABASE_URL in `.env` file
- Ensure PostgreSQL/TimescaleDB is running
- Test connection: `psql -h localhost -U etl_user -d etl_db`

### No data returned
- Verify ETL pipeline has run: `python main.py`
- Check database has data: `SELECT COUNT(*) FROM stock_prices;`
- Confirm symbol names are correct and uppercase

---

## License & Contact

For additional features, bug reports, or questions, please open an issue on GitHub.
