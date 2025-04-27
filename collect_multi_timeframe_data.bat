@echo off
:: Multi-Timeframe Market Data Collection Batch File
:: :ArchitecturalPattern :CommandLineInterface
:: :Context :DataCollection for market data across multiple timeframes
::
:: This script runs the multi-timeframe data collector for all market indices and commodities
:: at various timeframes, respecting API limitations

echo Starting Multi-Timeframe Market Data Collection...

:: Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

:: Run the collector with all default symbols and all timeframes
python data_collection\collect_multi_timeframe_data.py --all --timeframes 1day,60min,30min,15min,5min,1min --verbose

echo Collection process completed. See logs for details.
pause