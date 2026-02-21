import time
import datetime
import pandas as pd
<<<<<<< HEAD
from sqlalchemy import create_engine, text
import logging
from typing import List, Optional

from src.config.settings import Config
from src.extractors.yahoo_finance import AlphaVantage_Extractor
=======
from sqlalchemy import create_engine, engine as sqla_engine
import logging
import time
from typing import List, Optional

from src.config.settings import Config
from src.extractors.yahoo_finance import YahooFinanceExtractor
>>>>>>> 5a3e844c5cb787835348adb59c0e9096803e0066
from src.transformers.financial_metrics import apply_transformations
from src.monitoring.metrics import MetricsCollector

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

<<<<<<< HEAD

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
=======
def create_database_engine(config: Config) -> sqla_engine.Engine:
    """Create and return a SQLAlchemy database engine."""
    return create_engine(config.DATABASE_URL())


def load_to_database(df: pd.DataFrame, engine: sqla_engine.Engine, table_name: str = 'stock_prices') -> int:
    """Load DataFrame to database table.

    Args:
        df: DataFrame to load
        engine: SQLAlchemy engine
        table_name: Target table name

    Returns:
        Number of rows loaded
    """
    df.to_sql(table_name, engine, if_exists='append', index=False)
    rows_loaded = len(df)
    logger.info(f'Loaded {rows_loaded} rows into {table_name}')
    return rows_loaded


def run_etl(
    engine: Optional[sqla_engine.Engine] = None,
    symbols: Optional[List[str]] = None,
    period: str = '1mo',
    metrics_collector: Optional[MetricsCollector] = None
) -> int:
    """Extract, transform, and load stock price data.

    Args:
        engine: Optional SQLAlchemy engine (created if not provided)
        symbols: List of stock symbols to extract (defaults to config symbols)
        period: Time period for extraction (default: '1mo')
        metrics_collector: Optional metrics collector for tracking

    Returns:
        Number of rows loaded to database
    """
    config = Config()
    symbols = symbols or config.STOCK_SYMBOLS
    metrics_collector = metrics_collector or MetricsCollector()

    extractor = YahooFinanceExtractor(symbols, metrics_collector=metrics_collector)
>>>>>>> 5a3e844c5cb787835348adb59c0e9096803e0066

    engine = engine or create_engine(config.DATABASE_URL())
    _ensure_runs_table(engine)

    start = time.monotonic()
    try:
<<<<<<< HEAD
        df = extractor.extract_all(outputsize=outputsize)
        if df.empty:
            logger.info('No data extracted; nothing to load')
            _log_run(engine, symbols, 0, time.monotonic() - start, 'no_data')
=======
        # Extract
        df = extractor.extract_all(period=period)
        if df.empty:
            logger.info('No data extracted; nothing to load')
            metrics_collector.finalize(success=True)
>>>>>>> 5a3e844c5cb787835348adb59c0e9096803e0066
            return 0

        # Transform
        df = apply_transformations(df, metrics_collector=metrics_collector)

<<<<<<< HEAD
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
=======
        # Load
        metrics_collector.start_load()

        conn_start = time.time()
        db_engine = engine or create_database_engine(config)
        conn_duration = time.time() - conn_start
        metrics_collector.record_database_connection(conn_duration)

        rows_loaded = load_to_database(df, db_engine)

        metrics_collector.end_load(rows_loaded, success=True)
        metrics_collector.finalize(success=True)

        return rows_loaded

    except Exception as e:
        logger.exception('Error during ETL pipeline')
        metrics_collector.end_load(0, success=False, error=str(e))
        metrics_collector.finalize(success=False)
>>>>>>> 5a3e844c5cb787835348adb59c0e9096803e0066
        return 0


if __name__ == '__main__':
<<<<<<< HEAD
    rows = run_etl()
    print(f'ETL finished. Rows loaded: {rows}')
=======
    collector = MetricsCollector()
    rows = run_etl(metrics_collector=collector)
    print(f'ETL finished. Rows loaded: {rows}')
    print('\n' + collector.get_formatted_summary())
>>>>>>> 5a3e844c5cb787835348adb59c0e9096803e0066
