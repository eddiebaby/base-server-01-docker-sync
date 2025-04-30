@echo off
REM Script to run the Mock Schwab API OAuth example
REM This demonstrates the OAuth authentication flow using mock implementations

echo Mock Schwab API OAuth Demo Runner
echo ================================
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
echo Running Mock Schwab API OAuth Demo...
echo.

python examples/mock_oauth_demo.py

echo.
echo Demo completed.
echo.

pause