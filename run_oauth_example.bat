@echo off
REM Script to run the Schwab API OAuth example
REM This demonstrates the OAuth authentication flow

echo Schwab API OAuth Example Runner
echo ==============================
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
pip show requests >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing required packages...
    pip install -r requirements.txt
    if %ERRORLEVEL% NEQ 0 (
        echo Error installing packages. Please check your Python installation.
        goto :eof
    )
)

echo.
echo Do you want to use the real Schwab API or the mock implementation?
echo 1. Real Schwab API (requires valid credentials)
echo 2. Mock implementation (for demonstration purposes)
echo.

choice /c 12 /n /m "Enter your choice (1 or 2): "
set choice=%errorlevel%

if "%choice%"=="1" (
    echo.
    echo Running Schwab API OAuth Example with real API...
    echo.
    
    choice /c yn /n /m "Configure credentials? (y/n): "
    set config_creds=%errorlevel%
    
    if "%config_creds%"=="1" (
        call setup_schwab_credentials.bat
    )
    
    echo.
    echo Running OAuth example...
    python examples/schwab_oauth_simplified.py
) else (
    echo.
    echo Running Mock Schwab API OAuth Demo...
    echo.
    python examples/mock_oauth_demo.py
)

echo.
echo Example completed.
echo.

choice /c yn /n /m "Would you like to run more examples? (y/n): "
set more_examples=%errorlevel%

if "%more_examples%"=="1" (
    echo.
    echo Available examples:
    echo 1. OAuth Demo
    echo 2. Market Data Example
    echo 3. Run OAuth Tests
    echo.
    
    choice /c 123 /n /m "Enter your choice (1, 2, or 3): "
    set example_choice=%errorlevel%
    
    if "%example_choice%"=="1" (
        python examples/oauth_demo.py
    ) else if "%example_choice%"=="2" (
        python examples/market_data_example.py
    ) else if "%example_choice%"=="3" (
        call run_oauth_tests.bat
    )
)

echo.
echo Done.
echo.

pause