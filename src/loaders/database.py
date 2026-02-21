import time
import pandas as pd
from sqlalchemy import create_engine, text
import logging
from typing import List, Optional

from src.config.settings import Config
from src.extractors.yahoo_finance import AlphaVantage_Extractor
from src.transformers.financial_metrics import apply_transformations

logger = logging.getLogger(__name__)

_CREATE_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS etl_runs (
    id            SERIAL PRIMARY KEY,
    run_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    symbols       TEXT        NOT NULL,
    rows_loaded   INTEGER     NOT NULL,
    duration_secs FLOAT       NOT NULL,
    status        VARCHAR(16) NOT NULL,
    error_message TEXT
);
"""


def _ensure_runs_table(engine):
    with engine.begin() as conn:
        conn.execute(text(_CREATE_RUNS_TABLE))


def _log_run(engine, symbols, rows_loaded, duration_secs, status, error_message=None):
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO etl_runs (symbols, rows_loaded, duration_secs, status, error_message) "
                "VALUES (:symbols, :rows, :dur, :status, :err)"
            ),
            {
                "symbols": ",".join(symbols),
                "rows": rows_loaded,
                "dur": round(duration_secs, 2),
                "status": status,
                "err": error_message,
            },
        )


def run_etl(engine=None, symbols: Optional[List[str]] = None, outputsize: str = 'compact') -> int:
    """Extract, transform, load pipeline. Returns number of rows written."""
    config = Config()
    symbols = symbols or config.STOCK_SYMBOLS
    extractor = AlphaVantage_Extractor(symbols)

    engine = engine or create_engine(config.DATABASE_URL())
    _ensure_runs_table(engine)

    start = time.monotonic()
    try:
        df = extractor.extract_all(outputsize=outputsize)
        if df.empty:
            logger.info('No data extracted; nothing to load')
            _log_run(engine, symbols, 0, time.monotonic() - start, 'no_data')
            return 0

        df = apply_transformations(df)

        db_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol']
        df = df[[c for c in db_cols if c in df.columns]]

        df.to_sql('stock_prices', engine, if_exists='append', index=False)
        duration = time.monotonic() - start
        logger.info(f'Loaded {len(df)} rows into stock_prices')
        _log_run(engine, symbols, len(df), duration, 'success')
        return len(df)

    except Exception as exc:
        duration = time.monotonic() - start
        logger.exception('Error during run_etl')
        _log_run(engine, symbols, 0, duration, 'error', str(exc))
        return 0


if __name__ == '__main__':
    rows = run_etl()
    print(f'ETL finished. Rows loaded: {rows}')
