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
echo Running Schwab API OAuth Example...
echo.

set /p option="Configure credentials? (y/n): "
if /i "%option%"=="y" (
    python examples/schwab_oauth_simplified.py --save-credentials
) else (
    python examples/schwab_oauth_simplified.py
)

echo.
echo Example completed.
echo.

set /p run_more="Would you like to run more examples? (y/n): "
if /i not "%run_more%"=="y" goto :eof

echo.
echo Available examples:
echo 1. Standard OAuth Demo
echo 2. Exit
echo.

set /p example="Select an example to run (1-2): "
if "%example%"=="1" (
    python examples/oauth_demo.py
) else if "%example%"=="2" (
    goto :eof
) else (
    echo Invalid selection.
)

echo.
echo Done.