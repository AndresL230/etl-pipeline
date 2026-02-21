ETL Pipeline
============

![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen)
![Python](https://img.shields.io/badge/Language-Python_3.12-yellow)
![Alpha Vantage](https://img.shields.io/badge/Data-Alpha_Vantage-blue)
![TimescaleDB](https://img.shields.io/badge/DB-TimescaleDB-orange)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red)

Overview
--------

A Python ETL pipeline that extracts historical stock price data from Alpha Vantage,
computes financial metrics (daily returns, 7-day SMA), and loads results into a
TimescaleDB (PostgreSQL) hypertable. A Streamlit dashboard shows ETL run history
and lets you browse the loaded data.

Architecture
------------

```
  .env
   |
   v
Config (src/config/settings.py)
   |                    |
   | API key            | DB URL
   v                    v
+------------------+    +-------------------------+
| AlphaVantage     |    |                         |
| _Extractor       |    |   run_etl()             |
| yahoo_finance.py |    |   loaders/database.py   |
+------------------+    +-------------------------+
        |                         ^         |
        | DataFrame               |         |
        v                         |         |
+------------------+   DataFrame  |         |
| apply_transform- |              |         |
| ations()         |--------------+         |
| financial_       |                        |
| metrics.py       |             INSERT     |
+------------------+                        |
                                            v
                              +------------------------+
                              |  TimescaleDB (Docker)  |
                              |------------------------|
                              |  stock_prices          |
                              |  (hypertable)          |
                              |                        |
                              |  etl_runs              |
                              |  (run history)         |
                              +------------------------+
                                            |
                                    SELECT  |
                                            v
                              +------------------------+
                              |  Streamlit Dashboard   |
                              |  dashboard/app.py      |
                              |------------------------|
                              |  Tab 1: ETL Statistics |
                              |  Tab 2: Data Table     |
                              +------------------------+
```

Project Structure
-----------------

```
etl-pipeline/
├── main.py                          # ETL entrypoint
├── requirements.txt
├── docker-compose.yml               # TimescaleDB container
├── init.sql                         # DB schema (stock_prices hypertable)
├── .env                             # Credentials (not committed)
├── data/
│   └── extracted_data_test.csv      # Sample data for local testing
├── scripts/
│   └── run_transform_check.py       # Transform validation (no DB needed)
├── dashboard/
│   └── app.py                       # Streamlit dashboard
├── tests/
│   └── test_transform.py            # 18 unit + integration tests
└── src/
    ├── config/
    │   └── settings.py              # Config from environment variables
    ├── extractors/
    │   └── yahoo_finance.py         # AlphaVantage_Extractor
    ├── transformers/
    │   └── financial_metrics.py     # daily_return, sma_7
    └── loaders/
        └── database.py              # run_etl(), etl_runs logging
```

Tech Stack
----------

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Data source | Alpha Vantage REST API              |
| Processing  | Python 3.12, pandas, numpy          |
| Database    | TimescaleDB (PostgreSQL + extension) |
| ORM         | SQLAlchemy + psycopg2               |
| Dashboard   | Streamlit + Plotly                  |
| Config      | python-dotenv                       |
| Testing     | pytest (18 tests)                   |
| Container   | Docker / docker-compose             |

Quick Start
-----------

### 1. Clone and create a virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

### 2. Configure credentials

Create a `.env` file in the project root:

```
ALPHAVANTAGE_API_KEY=your_key_here   # https://www.alphavantage.co/support/#api-key
DB_HOST=localhost
DB_PORT=5432
DB_NAME=financial_data
DB_USER=etl_user
DB_PASSWORD=defaultpassword
```

### 3. Start the database

```powershell
docker-compose up -d
```

This starts a TimescaleDB container and runs `init.sql` to create the
`stock_prices` hypertable automatically.

### 4. Run the ETL pipeline

```powershell
python main.py
```

Extracts 100 trading days of data for AAPL, GOOGL, MSFT (configurable via
`STOCK_SYMBOLS` in `.env`), computes metrics, and loads to TimescaleDB.
Each run is logged to the `etl_runs` table.

### 5. Launch the dashboard

```powershell
.venv\Scripts\streamlit.exe run dashboard\app.py
```

Opens at http://localhost:8501

Local Transform Check (no DB required)
---------------------------------------

```powershell
.venv\Scripts\python.exe scripts\run_transform_check.py
```

Reads `data/extracted_data_test.csv` and validates the transformation output.
Exit code 0 = pass, non-zero = failure (CI-friendly).

Tests
-----

```powershell
python -m pytest -q
```

18 tests covering transformers, the Alpha Vantage extractor (mocked), and ETL
integration (mocked DB).

Configuration
-------------

All configuration is read from environment variables (via `.env`):

| Variable              | Default        | Description                        |
|-----------------------|----------------|------------------------------------|
| `ALPHAVANTAGE_API_KEY`| —              | Alpha Vantage API key (required)   |
| `DB_HOST`             | localhost       | PostgreSQL host                    |
| `DB_PORT`             | 5432           | PostgreSQL port                    |
| `DB_NAME`             | financial_data | Database name                      |
| `DB_USER`             | etl_user       | Database user                      |
| `DB_PASSWORD`         | —              | Database password (required)       |
| `STOCK_SYMBOLS`       | AAPL,GOOGL,MSFT| Comma-separated ticker list        |
| `LOG_LEVEL`           | INFO           | Logging level                      |

Database Schema
---------------

**stock_prices** (TimescaleDB hypertable, partitioned by timestamp)

| Column        | Type           |
|---------------|----------------|
| id            | SERIAL PK      |
| symbol        | VARCHAR(10)    |
| timestamp     | TIMESTAMPTZ    |
| open          | DECIMAL(10,2)  |
| high          | DECIMAL(10,2)  |
| low           | DECIMAL(10,2)  |
| close         | DECIMAL(10,2)  |
| volume        | BIGINT         |
| created_at    | TIMESTAMPTZ    |

**etl_runs** (created automatically on first ETL run)

| Column        | Type           |
|---------------|----------------|
| id            | SERIAL PK      |
| run_at        | TIMESTAMPTZ    |
| symbols       | TEXT           |
| rows_loaded   | INTEGER        |
| duration_secs | FLOAT          |
| status        | VARCHAR(16)    |
| error_message | TEXT           |

API Rate Limits
---------------

Alpha Vantage free tier: **25 requests/day**, 1 request/second.
The extractor adds a 1.2s delay between symbols to stay within the per-second limit.
With the default 3 symbols, each ETL run costs 3 of your 25 daily requests.

Troubleshooting
---------------

**No data extracted** — Alpha Vantage daily quota (25 req/day) may be exhausted.
Wait until the next day or upgrade to a paid plan.

**psycopg2 not found** — Install separately: `.venv\Scripts\pip install psycopg2-binary`

**DB connection refused** — Ensure Docker is running: `docker-compose up -d`

**Merge conflicts in source files** — The project uses a single `main` branch.
If conflicts appear, keep the HEAD version (Alpha Vantage implementation).

Future Enhancements
-------------------

- Scheduled runs (Apache Airflow)
- Data quality validation (Great Expectations)
- Prometheus metrics export
- Incremental loading (delta-only updates)
- More financial indicators (RSI, MACD, Bollinger Bands)
