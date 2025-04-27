#!/usr/bin/env python3
"""
Simple test to fetch data from Yahoo Finance
"""
import sys
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

def test_yfinance_fetch():
    """Test basic Yahoo Finance data fetching"""
    symbol = "^GSPC"  # S&P 500
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    print(f"Fetching data for {symbol} from {start_date} to {end_date}")
    
    try:
        # Initialize ticker
        ticker = yf.Ticker(symbol)
        
        # Fetch daily data
        daily_data = ticker.history(start=start_date, end=end_date, interval="1d")
        print(f"\nDaily data: {len(daily_data)} rows")
        if not daily_data.empty:
            print(daily_data.head(2))
        
        # Fetch hourly data
        hourly_data = ticker.history(start=start_date, end=end_date, interval="1h")
        print(f"\nHourly data: {len(hourly_data)} rows")
        if not hourly_data.empty:
            print(hourly_data.head(2))
        
        # Fetch 5-minute data (limited history)
        minute_data = ticker.history(start=start_date, end=end_date, interval="5m")
        print(f"\n5-minute data: {len(minute_data)} rows")
        if not minute_data.empty:
            print(minute_data.head(2))
            
        return True
    except Exception as e:
        print(f"Error fetching data: {e}")
        return False

if __name__ == "__main__":
    print("=== Yahoo Finance Data Fetch Test ===\n")
    success = test_yfinance_fetch()
    
    if success:
        print("\n✅ Yahoo Finance data fetch test successful")
        sys.exit(0)
    else:
        print("\n❌ Yahoo Finance data fetch test failed")
        sys.exit(1)