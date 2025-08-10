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

    STOCK_SYMBOLS = os.getenv('STOCK_SYMBOLS').split(',')

    def DATABASE_URL(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"