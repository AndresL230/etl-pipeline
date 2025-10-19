import pandas as pd
from sqlalchemy import create_engine, text
import logging
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import Config
from extractors.yahoo_finance import YFinance_Extractor

config = Config()
extractor = YFinance_Extractor(config.STOCK_SYMBOLS)
try:
    engine = create_engine(config.DATABASE_URL())
    # Extract
    df = extractor.extract_all()

    if df.empty:
        print("No data extracted; nothing to load")
    else:
        # Load into the TimescaleDB hypertable named `stock_prices`
        df.to_sql("stock_prices", engine, if_exists="append", index=False)
        print(f"Loaded {len(df)} rows into stock_prices")

except Exception as e:
    print(f"Error connecting to database or loading data: {e}")