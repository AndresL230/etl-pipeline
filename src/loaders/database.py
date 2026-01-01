import pandas as pd
from sqlalchemy import create_engine
import logging
import os
import time
from typing import List, Optional

from src.config.settings import Config
from src.extractors.yahoo_finance import YFinance_Extractor
from src.transformers.financial_metrics import apply_transformations
from src.monitoring.metrics import MetricsCollector

logger = logging.getLogger(__name__)


def run_etl(engine=None, symbols: Optional[List[str]] = None, period: str = '1mo', metrics_collector: Optional[MetricsCollector] = None) -> int:
    """Extract, transform, load pipeline.

    Returns number of rows written.
    """
    config = Config()
    symbols = symbols or config.STOCK_SYMBOLS

    if metrics_collector is None:
        metrics_collector = MetricsCollector()

    extractor = YFinance_Extractor(symbols, metrics_collector=metrics_collector)

    try:
        df = extractor.extract_all(period=period)
        if df.empty:
            logger.info('No data extracted; nothing to load')
            metrics_collector.finalize(success=True)
            return 0

        df = apply_transformations(df, metrics_collector=metrics_collector)

        metrics_collector.start_load()

        conn_start = time.time()
        engine = engine or create_engine(config.DATABASE_URL())
        conn_duration = time.time() - conn_start
        metrics_collector.record_database_connection(conn_duration)

        df.to_sql('stock_prices', engine, if_exists='append', index=False)
        logger.info(f'Loaded {len(df)} rows into stock_prices')

        metrics_collector.end_load(len(df), success=True)
        metrics_collector.finalize(success=True)

        return len(df)

    except Exception as e:
        logger.exception('Error during run_etl')
        if metrics_collector:
            metrics_collector.end_load(0, success=False, error=str(e))
            metrics_collector.finalize(success=False)
        return 0


if __name__ == '__main__':
    collector = MetricsCollector()
    rows = run_etl(metrics_collector=collector)
    print(f'ETL finished. Rows loaded: {rows}')
    print('\n' + collector.get_formatted_summary())