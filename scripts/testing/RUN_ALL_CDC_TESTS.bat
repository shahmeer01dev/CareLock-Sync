@echo off
echo.
echo ═══════════════════════════════════════════════════════════════
echo   CDC v3 — Final Verification After SQL Fix
echo ═══════════════════════════════════════════════════════════════
echo.

cd /d C:\Projects\CareLock-Sync

echo [INFO] Running all 65 tests...
echo.

pytest tests\unit\test_cdc_monitor.py tests\unit\test_cdc_performance.py tests\unit\test_cdc_v3_specific.py -v --tb=short

echo.
echo ═══════════════════════════════════════════════════════════════
echo   Test run complete - check results above
echo ═══════════════════════════════════════════════════════════════
echo.
pause
