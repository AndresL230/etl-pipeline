import yfinance as yf
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YFinance_Extractor:
    def __init__(self, symbols):
        self.symbols = symbols

    def extract_daily_data(self, symbol, period = '1mo'):
        try:
            logger.info(f"Extracting data for {symbol}")
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)

            if data.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            
            data['symbol'] = symbol
            data['timestamp'] = data.index
            data.reset_index(drop=True, inplace=True)

            data.columns = [col.lower().replace(' ', '_') for col in data.columns]

            logger.info(f"Extracted {len(data)} records for {symbol}")
            return data
        
        except Exception as e:
            logger.error(f"Error extracting data for {symbol}: {str(e)}")
            return pd.DataFrame()
        
    def extract_all(self, period = '1mo'):
        all_data = []

        for symbol in self.symbols:
            data = self.extract_daily_data(symbol, period)
            if not data.empty:
                all_data.append(data)
            
        if all_data:
            combined_data = pd.concat(all_data, ignore_index=True)
            logger.info(F"Total records extracted: {len(combined_data)}")
            return combined_data
        else:
            logger.warning("No data extracted for any symbol")
            return pd.DataFrame()
