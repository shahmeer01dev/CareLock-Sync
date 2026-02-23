@echo off
REM Add Oracle Instant Client to System PATH permanently
REM Run this as Administrator

echo Adding Oracle Instant Client to System PATH...
echo.

set ORACLE_PATH=C:\oracle\instantclient_23_0

REM Check if already in PATH
echo %PATH% | findstr /C:"%ORACLE_PATH%" >nul
if %errorlevel% equ 0 (
    echo Oracle Instant Client already in PATH
) else (
    REM Add to system PATH
    setx /M PATH "%PATH%;%ORACLE_PATH%"
    if %errorlevel% equ 0 (
        echo [OK] Added to System PATH successfully
        echo.
        echo IMPORTANT: You must restart your terminal/IDE for changes to take effect
    ) else (
        echo [ERROR] Failed to add to PATH. Please run as Administrator.
        echo.
        echo Manual steps:
        echo 1. Right-click "This PC" and select Properties
        echo 2. Click "Advanced system settings"
        echo 3. Click "Environment Variables"
        echo 4. Under "System variables", find and edit "Path"
        echo 5. Add: %ORACLE_PATH%
    )
)

echo.
echo Testing Oracle Instant Client...
echo.

REM Set for current session
set PATH=%ORACLE_PATH%;%PATH%

REM Test with Python
python -c "import cx_Oracle; print('cx_Oracle version:', cx_Oracle.version)"

echo.
echo Setup complete!
pause
