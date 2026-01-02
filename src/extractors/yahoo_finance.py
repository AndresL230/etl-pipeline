import yfinance as yf
import pandas as pd
import logging
import time
from typing import List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        try:
            logger.info(f"Extracting data for {symbol}")
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)

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