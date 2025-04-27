@echo off
:: File-Based Market Data Collection Batch File
:: :ArchitecturalPattern :CommandLineInterface
:: :Context :DataCollection for market data across multiple timeframes
::
:: This script runs the file-based multi-timeframe data collector that
:: stores data in CSV files without requiring a database connection

echo === File-Based Multi-Timeframe Market Data Collection ===

:: First run a simple test to make sure the system works
echo.
echo Step 1: Testing the file-based collector...
python test_file_based_collector.py
if %ERRORLEVEL% NEQ 0 (
    echo Error running the test. Please check the output above for details.
    pause
    exit /b 1
)

:: Now collect data for all symbols
echo.
echo Step 2: Collecting data for all symbols...
python -c "import sys; from data_collection.file_based_multi_timeframe_collector import FileBasedMultiTimeframeCollector; collector = FileBasedMultiTimeframeCollector(); results = collector.collect_multi_timeframe_data(symbols=['^GSPC', '^VIX', '^VXN', '^SKEW', '^VVIX', '^TNX', '^NDX', '^RUT', 'CL=F', 'GC=F', 'HG=F'], timeframes=['1day', '60min', '30min', '15min', '5min', '1min'], start_date='2023-01-01', end_date=None); print(f'Processed {results[\"symbols_processed\"]} symbols, {results[\"total_rows_stored\"]} rows stored.')"

echo.
echo Collection process completed. Data stored in market_data directory.
pause