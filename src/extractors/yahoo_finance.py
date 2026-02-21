import time
import requests
import pandas as pd
import logging
import time
from typing import List, Optional

from src.config.settings import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

<<<<<<< HEAD
BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantage_Extractor:
    def __init__(self, symbols):
        self.symbols = symbols
        self.api_key = Config.ALPHAVANTAGE_API_KEY

    def extract_daily_data(self, symbol, outputsize='compact'):
=======

class YahooFinanceExtractor:
    """Extractor for fetching stock price data from Yahoo Finance."""

    def __init__(self, symbols: List[str], metrics_collector=None):
        """Initialize the extractor.

        Args:
            symbols: List of stock ticker symbols to extract
            metrics_collector: Optional MetricsCollector for tracking extraction metrics
        """
        self.symbols = symbols
        self.metrics_collector = metrics_collector

    def extract_daily_data(self, symbol: str, period: str = '1mo') -> pd.DataFrame:
        """Extract historical price data for a single symbol.

        Args:
            symbol: Stock ticker symbol
            period: Time period for historical data (e.g., '1mo', '1y')

        Returns:
            DataFrame with normalized price data, or empty DataFrame on failure
        """
        start_time = time.time()
>>>>>>> 5a3e844c5cb787835348adb59c0e9096803e0066
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

<<<<<<< HEAD
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
=======
            duration = time.time() - start_time

            if data.empty:
                logger.warning(f"No data found for {symbol}")
                self._record_extraction_metrics(symbol, 0, duration, success=False)
                return pd.DataFrame()

            # Normalize data structure
            data['symbol'] = symbol
            data['timestamp'] = data.index
            data.reset_index(drop=True, inplace=True)
            data.columns = [col.lower().replace(' ', '_') for col in data.columns]

            logger.info(f"Extracted {len(data)} records for {symbol}")
            self._record_extraction_metrics(symbol, len(data), duration, success=True)

            return data

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error extracting data for {symbol}: {str(e)}")
            self._record_extraction_metrics(symbol, 0, duration, success=False)
            return pd.DataFrame()

    def extract_all(self, period: str = '1mo') -> pd.DataFrame:
        """Extract historical data for all configured symbols.

        Args:
            period: Time period for historical data (e.g., '1mo', '1y')

        Returns:
            Combined DataFrame with data from all symbols
        """
        if self.metrics_collector:
            self.metrics_collector.start_extraction(len(self.symbols))

        all_data = []
        for symbol in self.symbols:
            data = self.extract_daily_data(symbol, period)
            if not data.empty:
                all_data.append(data)

        if self.metrics_collector:
            self.metrics_collector.end_extraction()

        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            logger.info(f"Total records extracted: {len(combined_data)}")
            return combined_data
        else:
            logger.warning("No data extracted for any symbol")
            return pd.DataFrame()

    def _record_extraction_metrics(self, symbol: str, rows: int, duration: float, success: bool) -> None:
        """Record extraction metrics for a symbol if collector is available."""
        if self.metrics_collector:
            self.metrics_collector.record_symbol_extraction(symbol, rows, duration, success)
>>>>>>> 5a3e844c5cb787835348adb59c0e9096803e0066
