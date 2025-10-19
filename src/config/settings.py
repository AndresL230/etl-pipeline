import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'financial_data')
    DB_USER = os.getenv('DB_USER', 'etl_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD')

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Parse STOCK_SYMBOLS safely. If not provided, use a sensible default list.
    _symbols_raw = os.getenv('STOCK_SYMBOLS')
    if _symbols_raw and _symbols_raw.strip():
        STOCK_SYMBOLS = [s.strip() for s in _symbols_raw.split(',') if s.strip()]
    else:
        STOCK_SYMBOLS = ["AAPL", "GOOGL", "MSFT"]

    def DATABASE_URL(self):
        # Note: keep DB_PASSWORD secret; callers should avoid printing it.
        pwd = self.DB_PASSWORD or ''
        return f"postgresql://{self.DB_USER}:{pwd}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"