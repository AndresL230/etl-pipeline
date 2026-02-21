import time
import requests
import pandas as pd
import logging

from src.config.settings import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantage_Extractor:
    def __init__(self, symbols):
        self.symbols = symbols
        self.api_key = Config.ALPHAVANTAGE_API_KEY

    def extract_daily_data(self, symbol, outputsize='compact'):
        try:
            logger.info(f"Extracting data for {symbol}")
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'outputsize': outputsize,
                'apikey': self.api_key,
            }
            resp = requests.get(BASE_URL, params=params, timeout=15)
            resp.raise_for_status()
            payload = resp.json()

            if 'Time Series (Daily)' not in payload:
                msg = payload.get('Note') or payload.get('Information') or payload.get('Error Message', 'Unknown error')
                logger.warning(f"No data for {symbol}: {msg}")
                return pd.DataFrame()

            ts = payload['Time Series (Daily)']
            rows = [
                {
                    'timestamp': pd.to_datetime(date_str),
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'volume': int(values['5. volume']),
                    'symbol': symbol,
                }
                for date_str, values in ts.items()
            ]

            df = pd.DataFrame(rows).sort_values('timestamp').reset_index(drop=True)
            logger.info(f"Extracted {len(df)} records for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error extracting data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def extract_all(self, outputsize='compact'):
        all_data = []

        for i, symbol in enumerate(self.symbols):
            if i > 0:
                time.sleep(1.2)
            data = self.extract_daily_data(symbol, outputsize)
            if not data.empty:
                all_data.append(data)

        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            logger.info(f"Total records extracted: {len(combined)}")
            return combined
        else:
            logger.warning("No data extracted for any symbol")
            return pd.DataFrame()
