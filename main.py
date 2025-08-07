# test_basic.py
import pandas as pd
import yfinance as yf
from sqlalchemy import create_engine

# Test yfinance
ticker = yf.Ticker("AAPL")
data = ticker.history(period="5d")
print(f"✅ Got {len(data)} records for AAPL")

# Test pandas
df = pd.DataFrame(data)
print(f"✅ Pandas working with {len(df)} rows")

print("🎉 Ready to build your ETL pipeline!")