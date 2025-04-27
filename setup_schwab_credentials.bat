@echo off
REM Script to set up Schwab API credentials
REM This guides users through setting up their credentials for authentication

echo Schwab API Credentials Setup
echo ===========================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found. Please install Python 3.10 or higher.
    goto :eof
)

REM Run the credentials setup utility
echo Running credentials setup utility...
echo.

python schwab_api/utils/setup_credentials.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error running the setup utility. Please check your Python installation.
    goto :eof
)

echo.
echo Setup completed.
echo.
echo You can now use the Schwab API with your credentials.
echo To test the authentication, run one of the example scripts:
echo   - run_oauth_example.bat
echo.