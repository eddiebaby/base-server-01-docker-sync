@echo off
REM Script to run OAuth tests to verify the setup
REM This script runs the OAuth tests to ensure the configuration is correct

echo Schwab API OAuth Tests
echo ====================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found. Please install Python 3.10 or higher.
    goto :eof
)

REM Check if pytest is installed
python -c "import pytest" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Installing pytest...
    pip install pytest
    if %ERRORLEVEL% NEQ 0 (
        echo Error installing pytest. Please check your Python installation.
        goto :eof
    )
)

echo.
echo Running OAuth tests...
echo.

REM Run the OAuth tests
python -m pytest tests/schwab_api/test_oauth_integration.py -v

echo.
echo Tests completed.
echo.

REM Check if mock demo exists
if exist "examples\mock_oauth_demo.py" (
    echo Running mock OAuth demo to verify functionality...
    echo.
    python examples/mock_oauth_demo.py
    echo.
)

echo.
echo All tests completed.
echo.

pause