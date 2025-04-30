@echo off
REM Script to set up Schwab API OAuth credentials
REM This script guides users through the process of configuring their Schwab API credentials

echo Schwab API Credentials Setup
echo ===========================
echo.
echo This script will help you configure your Schwab API credentials for OAuth authentication.
echo You will need your Schwab API developer account credentials (client ID and client secret).
echo.

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python not found. Please install Python 3.10 or higher.
    goto :eof
)

REM Create config directory if it doesn't exist
if not exist "config" (
    echo Creating config directory...
    mkdir config
)

REM Create .env file if it doesn't exist
if not exist "config\.env" (
    echo Creating .env file...
    echo # Schwab API OAuth credentials > config\.env
)

echo.
echo Please enter your Schwab API credentials:
echo.

set /p client_id="Enter your Schwab API client ID: "
set /p client_secret="Enter your Schwab API client secret (input will be hidden): "

echo.
echo Saving credentials...

REM Update .env file with credentials
powershell -Command "$content = Get-Content -Path 'config\.env' -Raw; $content = $content -replace 'SCHWAB_CLIENT_ID=.*', 'SCHWAB_CLIENT_ID=%client_id%'; if ($content -notmatch 'SCHWAB_CLIENT_ID=') { $content += \"`nSCHWAB_CLIENT_ID=%client_id%\" }; $content = $content -replace 'SCHWAB_CLIENT_SECRET=.*', 'SCHWAB_CLIENT_SECRET=%client_secret%'; if ($content -notmatch 'SCHWAB_CLIENT_SECRET=') { $content += \"`nSCHWAB_CLIENT_SECRET=%client_secret%\" }; Set-Content -Path 'config\.env' -Value $content"

echo.
echo Credentials saved to config\.env
echo.

REM Verify credentials were saved
echo Verifying credentials...
findstr "SCHWAB_CLIENT_ID" config\.env >nul
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Client ID was not saved properly.
)

findstr "SCHWAB_CLIENT_SECRET" config\.env >nul
if %ERRORLEVEL% NEQ 0 (
    echo Warning: Client secret was not saved properly.
)

echo.
echo Setup complete!
echo.
echo You can now run the OAuth examples with your credentials:
echo - run_oauth_example.bat - Run the full OAuth example
echo - run_mock_oauth_demo.bat - Run the mock OAuth demo (no real credentials needed)
echo.

pause