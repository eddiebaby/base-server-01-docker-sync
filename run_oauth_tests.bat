@echo off
REM Script to run the Schwab API OAuth unit tests
REM This verifies the OAuth implementation's correctness

echo Schwab API OAuth Test Runner
echo ============================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found. Please install Python 3.10 or higher.
    goto :eof
)

REM Check Python version
python --version | findstr /r "3\.[1-9][0-9]" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Warning: This script requires Python 3.10 or higher.
    echo Current Python version:
    python --version
    echo.
    
    set /p continue="Continue anyway? (y/n): "
    if /i not "%continue%"=="y" goto :eof
)

echo Checking for required packages...
pip show pytest >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Error installing packages. Please check your Python installation.
        goto :eof
    )
)

echo.
echo Running Schwab API OAuth Tests...
echo.

REM Run unit tests with verbose output
python -m pytest tests/schwab_api/test_oauth_integration.py -v

echo.
echo Tests completed.
echo.

echo You can now use the OAuth implementation in your applications.
echo Run the example with: run_oauth_example.bat