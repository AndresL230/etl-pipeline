#!/usr/bin/env python3
"""
Test script for data extraction
Run this to verify your setup works
"""

import sys
import os
sys.path.append('src')

from src.extractors.yahoo_finance import YFinance_Extractor
from src.config.settings import Config

def test_extraction():
    """Test data extraction from Yahoo Finance"""
    print("🚀 Testing Financial Data Extraction")
    print("=" * 50)
    
    # Initialize config
    config = Config()
    print(f"📊 Symbols to extract: {config.STOCK_SYMBOLS}")
    
    # Initialize extractor
    extractor = YFinance_Extractor(config.STOCK_SYMBOLS)
    
    # Test single symbol first
    print(f"\n🔍 Testing single symbol extraction: AAPL")
    aapl_data = extractor.extract_daily_data("AAPL", period="5d")
    
    if not aapl_data.empty:
        print(f"✅ Success! Extracted {len(aapl_data)} records for AAPL")
        print("\n📈 Sample data:")
        print(aapl_data[['symbol', 'timestamp', 'close', 'volume']].head())
        print(f"\n📊 Data columns: {list(aapl_data.columns)}")
    else:
        print("❌ Failed to extract AAPL data")
        return False
    
    # Test all symbols
    print(f"\n🔍 Testing all symbols extraction...")
    all_data = extractor.extract_all(period="5d")
    
    if not all_data.empty:
        print(f"✅ Success! Extracted {len(all_data)} total records")
        print(f"📊 Symbols found: {all_data['symbol'].unique()}")
        
        # Show summary by symbol
        summary = all_data.groupby('symbol').agg({
            'close': ['count', 'last'],
            'volume': 'last'
        }).round(2)
        print(f"\n📈 Summary by symbol:")
        print(summary)
        
        # Save to CSV for inspection
        all_data.to_csv('data/extracted_data_test.csv', index=False)
        print(f"\n💾 Data saved to: data/extracted_data_test.csv")
        
        return True
    else:
        print("❌ Failed to extract data for any symbol")
        return False

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    
    success = test_extraction()
    
    if success:
        print("\n🎉 Extraction test completed successfully!")
        print("Next steps:")
        print("1. Set up database (docker-compose up -d)")
        print("2. Create database loader")
        print("3. Build transformation pipeline")
    else:
        print("\n❌ Extraction test failed. Check your internet connection and try again.")