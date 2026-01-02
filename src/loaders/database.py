import pandas as pd
from sqlalchemy import create_engine, engine as sqla_engine
import logging
import time
from typing import List, Optional

from src.config.settings import Config
from src.extractors.yahoo_finance import YahooFinanceExtractor
from src.transformers.financial_metrics import apply_transformations
from src.monitoring.metrics import MetricsCollector

logger = logging.getLogger(__name__)


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

    try:
        # Extract
        df = extractor.extract_all(period=period)
        if df.empty:
            logger.info('No data extracted; nothing to load')
            metrics_collector.finalize(success=True)
            return 0

        # Transform
        df = apply_transformations(df, metrics_collector=metrics_collector)

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
        return 0


if __name__ == '__main__':
    collector = MetricsCollector()
    rows = run_etl(metrics_collector=collector)
    print(f'ETL finished. Rows loaded: {rows}')
    print('\n' + collector.get_formatted_summary())