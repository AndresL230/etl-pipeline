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
- Computation of daily returns and simple moving averages
- Preparing data for downstream analytics or loading into a time-series DB

Holdings Management (sample/data)
- Sample CSV dataset with multiple symbols for local testing (`data/extracted_data_test.csv`)

AI-Powered Insights (future)
- Placeholder for future AI/ML integrations to recommend portfolio actions

Technical Architecture
----------------------

Python ETL
- Extractors: `src/extractors/yahoo_finance.py` (yfinance wrapper)
- Transformers: `src/transformers/financial_metrics.py` (daily returns, SMA computation)
- Loaders: `src/loaders/database.py` (writes to `stock_prices` using SQLAlchemy and pandas)

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
├── init.sql                 # SQL used to initialize TimescaleDB (creates `stock_prices` hypertable)
├── docker-compose.yml      # Optional TimescaleDB compose service for local development
├── main.py                 # Entrypoint that calls run_etl()
├── requirements.txt        # Python dependencies (minimal, wheel-friendly)
├── data/
│   └── extracted_data_test.csv
├── scripts/
│   └── run_transform_check.py  # Manual transform check (no pytest required)
└── src/
	├── config/
	│   └── settings.py
	├── extractors/
	│   └── yahoo_finance.py
	├── transformers/
	│   └── financial_metrics.py
	└── loaders/
		└── database.py
```

API and Integration Notes
-------------------------

This repository is focused on the ETL portion of a stock analytics system. It does not ship a frontend or full portfolio management UI. For production integration you can expose an API or connect the output to an existing analytics stack.

Recommended external APIs for real-time price data:
- Alpha Vantage
- Finnhub
- Yahoo Finance (via `yfinance`)

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

Future Enhancements
-------------------

- Add an API layer to serve transformed metrics.
- Build a frontend dashboard for visualization.
- Add more transformation metrics and tests.

Troubleshooting
---------------

If the requirements installation fails due to `psycopg2-binary` or other build-time tools on Windows, install PostgreSQL developer libraries or comment the package and install the remaining dependencies.

Contact
-------
If you want more features (UI, API, additional transforms, CI), tell me which piece you want next and I will implement it.
