import yfinance as yf
import pandas as pd
import logging
import time
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YFinance_Extractor:
    def __init__(self, symbols, metrics_collector=None):
        self.symbols = symbols
        self.metrics_collector = metrics_collector

    def extract_daily_data(self, symbol, period = '1mo'):
        start_time = time.time()
        try:
            logger.info(f"Extracting data for {symbol}")
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)

            duration = time.time() - start_time

            if data.empty:
                logger.warning(f"No data found for {symbol}")
                if self.metrics_collector:
                    self.metrics_collector.record_symbol_extraction(symbol, 0, duration, success=False)
                return pd.DataFrame()

            data['symbol'] = symbol
            data['timestamp'] = data.index
            data.reset_index(drop=True, inplace=True)

            data.columns = [col.lower().replace(' ', '_') for col in data.columns]

            logger.info(f"Extracted {len(data)} records for {symbol}")

            if self.metrics_collector:
                self.metrics_collector.record_symbol_extraction(symbol, len(data), duration, success=True)

            return data

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error extracting data for {symbol}: {str(e)}")
            if self.metrics_collector:
                self.metrics_collector.record_symbol_extraction(symbol, 0, duration, success=False)
            return pd.DataFrame()
        
    def extract_all(self, period = '1mo'):
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
            logger.info(F"Total records extracted: {len(combined_data)}")
            return combined_data
        else:
            logger.warning("No data extracted for any symbol")
            return pd.DataFrame()