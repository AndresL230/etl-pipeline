import pandas as pd
from sqlalchemy import create_engine
import logging
import os
from typing import List, Optional

from config.settings import Config
from extractors.yahoo_finance import YFinance_Extractor
from transformers.financial_metrics import apply_transformations

logger = logging.getLogger(__name__)


def run_etl(engine=None, symbols: Optional[List[str]] = None, period: str = '1mo') -> int:
    """Extract, transform, load pipeline.

    Returns number of rows written.
    """
    config = Config()
    symbols = symbols or config.STOCK_SYMBOLS
    extractor = YFinance_Extractor(symbols)

    try:
        df = extractor.extract_all(period=period)
        if df.empty:
            logger.info('No data extracted; nothing to load')
            return 0

        df = apply_transformations(df)

        engine = engine or create_engine(config.DATABASE_URL())
        df.to_sql('stock_prices', engine, if_exists='append', index=False)
        logger.info(f'Loaded {len(df)} rows into stock_prices')
        return len(df)

    except Exception:
        logger.exception('Error during run_etl')
        return 0


if __name__ == '__main__':
    rows = run_etl()
    print(f'ETL finished. Rows loaded: {rows}')