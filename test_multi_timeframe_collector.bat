@echo off
:: Multi-Timeframe Market Data Collector Test Batch File
:: :ArchitecturalPattern :CommandLineInterface
:: :Context :Test for multi-timeframe data collection
::
:: This script applies the schema changes and runs tests to verify functionality

echo === Multi-Timeframe Market Data Collector Test ===

:: Step 1: Start PostgreSQL service if not running
echo.
echo Step 1: Ensuring PostgreSQL service is running...
net start postgresql-x64-14
if %ERRORLEVEL% NEQ 0 (
    echo PostgreSQL service not started. It might already be running or not installed.
    echo Continuing with the tests...
)

:: Step 2: Make sure psycopg2 is installed for database operations
echo.
echo Step 2: Checking for required Python packages...
pip install psycopg2-binary
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Could not install psycopg2-binary. Database operations may fail.
    echo Continuing with the tests...
)

:: Step 3: Apply schema changes using Python script
echo.
echo Step 3: Applying schema changes...
python apply_schema_changes.py
if %ERRORLEVEL% NEQ 0 (
    echo Error applying schema updates. Please check database connection.
    pause
    exit /b 1
)

:: Step 4: Run tests
echo.
echo Step 4: Running tests...
python test_multi_timeframe_collector.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo All tests passed! You can now run collect_multi_timeframe_data.bat
) else (
    echo Some tests failed. Check the output above for details.
)

pause