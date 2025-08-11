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

print(f"Using password: {config.DB_PASSWORD}")
print(f"Full database URL: {config.DATABASE_URL()}")
try:
    engine = create_engine(config.DATABASE_URL())
    extractor.extract_all().to_sql("stock_data", engine, if_exists="append", index=False)

except Exception as e:
    print(f"Error connecting to database: {e}")