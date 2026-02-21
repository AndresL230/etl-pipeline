ETL Pipeline
======================================

![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Language-Python-yellow)
![yfinance](https://img.shields.io/badge/Library-yfinance-blue)
![Pandas](https://img.shields.io/badge/Library-pandas-lightgrey)

Project Overview
----------------
This repository contains an ETL pipeline that extracts historical stock price data (via `yfinance`), applies basic financial transformations, and loads results into a PostgreSQL/TimescaleDB table.

Key Features
------------

Dashboard & Analytics (pipeline-focused)
- Extraction of historical price data for configured stock symbols
- **Advanced financial indicators**: RSI, MACD, Bollinger Bands, EMA, Volatility
- Multiple SMAs (7, 20, 50-day) and daily returns calculation
- Preparing data for downstream analytics or loading into a time-series DB
- **Comprehensive metrics tracking** for monitoring pipeline performance
- **REST API** for querying stock data and technical indicators

Holdings Management (sample/data)
- Sample CSV dataset with multiple symbols for local testing (`data/extracted_data_test.csv`)

AI-Powered Insights (future)
- Placeholder for future AI/ML integrations to recommend portfolio actions

Metrics & Monitoring
- Real-time tracking of extraction, transformation, and load metrics
- Automatic JSON export of pipeline metrics for analysis
- Per-symbol API response time tracking
- Data quality monitoring (null values, record counts)
- Formatted console output with detailed performance statistics

Technical Architecture
----------------------

Python ETL
- Extractors: `src/extractors/yahoo_finance.py` (yfinance wrapper)
- Transformers: `src/transformers/financial_metrics.py` (RSI, MACD, Bollinger Bands, SMA, EMA, Volatility)
- Loaders: `src/loaders/database.py` (writes to `stock_prices` using SQLAlchemy and pandas)
- Monitoring: `src/monitoring/metrics.py` (comprehensive metrics collection and reporting)
- API: `src/api/app.py` (FastAPI REST API for data access and technical indicators)

Quick Start Guide
-----------------

Prerequisites
- Python 3.12
- PowerShell (Windows) or a POSIX shell on macOS/Linux
- Optional: PostgreSQL client tools (for `psycopg2-binary` and local DB load)

Installation Steps (PowerShell)

1. Activate the repository virtual environment (if present):

```powershell
.venv\Scripts\Activate.ps1
```

If you do not have a `.venv` you can create one:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Upgrade packaging tools and install requirements:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

Note: `psycopg2-binary` may be commented out in `requirements.txt` to avoid build-time dependency on `pg_config`. If you need DB connectivity and `pg_config` is available (Postgres dev tools installed), install `psycopg2-binary` separately:

```powershell
python -m pip install psycopg2-binary
```

Run the ETL pipeline
--------------------

```powershell
python main.py
```

This will call `run_etl()` which extracts, transforms, and attempts to load into the `stock_prices` hypertable. If no DB is configured, run the local transform check instead.

The pipeline now includes automatic metrics tracking. After each run, you'll see:
- A formatted summary of pipeline performance
- Metrics saved to `metrics/etl_metrics_TIMESTAMP.json`

Demo Metrics (no DB required)
-----------------------------

To see the metrics tracking in action without database connectivity:

```powershell
python demo_metrics.py
```

This demonstrates all metrics features with mock data.

Run the API Server
------------------

Start the REST API to query stock data and technical indicators:

```powershell
python api_server.py
```

The API will be available at `http://localhost:8000`

Access the interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

See [API_GUIDE.md](API_GUIDE.md) for detailed endpoint documentation and usage examples.

Local transform check (no DB required)
------------------------------------

```powershell
.venv\Scripts\python.exe scripts\run_transform_check.py
```

Tests
-----
Run pytest inside the venv:

```powershell
.venv\Scripts\Activate.ps1
python -m pytest -q
```

Project Structure
-----------------

```
etl-pipeline/
├── README.md
├── METRICS_GUIDE.md        # Detailed metrics documentation
├── API_GUIDE.md            # REST API documentation
├── init.sql                # SQL used to initialize TimescaleDB
├── docker-compose.yml      # Optional TimescaleDB compose service
├── main.py                 # ETL pipeline entrypoint
├── api_server.py           # API server entrypoint
├── demo_metrics.py         # Demo script for metrics features
├── requirements.txt        # Python dependencies
├── data/
│   └── extracted_data_test.csv
├── scripts/
│   └── run_transform_check.py
├── metrics/                # Auto-generated metrics files (gitignored)
│   └── etl_metrics_*.json
├── tests/
│   ├── test_transform.py        # ETL pipeline tests
│   ├── test_metrics.py          # Metrics tracking tests
│   └── test_financial_indicators.py  # Financial indicators tests
└── src/
	├── config/
	│   └── settings.py
	├── extractors/
	│   └── yahoo_finance.py
	├── transformers/
	│   └── financial_metrics.py  # RSI, MACD, Bollinger Bands, etc.
	├── loaders/
	│   └── database.py
	├── monitoring/
	│   ├── __init__.py
	│   └── metrics.py
	└── api/
		├── __init__.py
		├── app.py          # FastAPI application
		└── models.py       # Pydantic models
```

API and Integration Notes
-------------------------

The project now includes a production-ready REST API built with FastAPI. Access stock data and technical indicators via HTTP endpoints.

**Key Endpoints:**
- `GET /api/v1/prices` - Stock prices with basic indicators
- `GET /api/v1/prices/advanced` - All advanced indicators (RSI, MACD, etc.)
- `GET /api/v1/symbols/{symbol}/summary` - Symbol statistics
- `GET /api/v1/indicators/{symbol}/{indicator}` - Specific indicators

**Technical Indicators Available:**
- SMA (Simple Moving Average) - 7, 20, 50 day
- EMA (Exponential Moving Average) - 12, 26 day
- RSI (Relative Strength Index) - Momentum oscillator
- MACD - Trend-following indicator with signal and histogram
- Bollinger Bands - Volatility bands
- Volatility - Rolling standard deviation of returns

See [API_GUIDE.md](API_GUIDE.md) for complete documentation.

Recommended external data sources:
- Yahoo Finance (via `yfinance`) - Free historical data
- Alpha Vantage - Real-time and historical data
- Finnhub - Stock fundamentals and news

Error Handling & Validation
---------------------------

- Transformer code validates for empty extraction results and logs warnings.
- Loader handles DB connection errors and logs exceptions.

Security Considerations
-----------------------

- Set DB credentials through environment variables or a `.env` file.
- Avoid printing secrets to logs.

Deployment
----------

For local testing you can run a TimescaleDB container via `docker-compose.yml` included in the repository. The database init script `init.sql` creates the `stock_prices` hypertable used by the loader.

Metrics Tracking
----------------

The pipeline includes comprehensive metrics tracking:

**What's Tracked:**
- Extraction: symbols processed, API response times, failed symbols, records per symbol
- Transformation: processing time, transformations applied, null values created
- Load: rows loaded, database connection time, load duration
- Pipeline: total duration, success/failure status

**Metrics Output:**
- Console: Formatted summary displayed after each run
- JSON Files: Timestamped files saved to `metrics/` directory
- Programmatic Access: Full metrics available via `MetricsCollector`

For detailed information, see [METRICS_GUIDE.md](METRICS_GUIDE.md)

Future Enhancements
-------------------

- Build a frontend dashboard for visualization (Streamlit/Grafana)
- WebSocket support for real-time price updates
- Implement alerting (email/Slack on failures)
- Add Prometheus metrics export for monitoring
- Historical trend analysis and anomaly detection
- Incremental loading strategy (delta-only updates)
- API authentication and rate limiting
- Redis caching for frequently accessed data
- Backtesting framework for trading strategies

Troubleshooting
---------------

If the requirements installation fails due to `psycopg2-binary` or other build-time tools on Windows, install PostgreSQL developer libraries or comment the package and install the remaining dependencies.

Contact
-------
If you want more features (UI, API, additional transforms, CI), tell me which piece you want next and I will implement it.
