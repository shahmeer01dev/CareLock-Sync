@echo off
echo.
echo ═══════════════════════════════════════════════════════════════
echo   CDC Monitor v3 — Quick Verification Test
echo ═══════════════════════════════════════════════════════════════
echo.

cd /d C:\Projects\CareLock-Sync

echo [1/4] Checking PostgreSQL connection...
python -c "import os; from sqlalchemy import create_engine; url = os.getenv('TEST_DB_URL') or os.getenv('HOSPITAL_DB_URL', 'postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db'); engine = create_engine(url); conn = engine.connect(); print('✓ PostgreSQL connected'); conn.close(); engine.dispose()" 2>nul
if errorlevel 1 (
    echo ✗ PostgreSQL not reachable
    echo.
    echo Set TEST_DB_URL or HOSPITAL_DB_URL environment variable
    echo Example: set TEST_DB_URL=postgresql://user:pass@localhost:5432/hospital_db
    echo.
    pause
    exit /b 1
)

echo.
echo [2/4] Running core CDC tests (40 tests)...
pytest tests\unit\test_cdc_monitor.py -v --tb=line -q
if errorlevel 1 (
    echo ✗ Core tests failed
    pause
    exit /b 1
)

echo.
echo [3/4] Running performance tests (14 tests)...
pytest tests\unit\test_cdc_performance.py -v --tb=line -q -s
if errorlevel 1 (
    echo ✗ Performance tests failed
    pause
    exit /b 1
)

echo.
echo [4/4] Running v3-specific tests (11 tests)...
pytest tests\unit\test_cdc_v3_specific.py -v --tb=line -q
if errorlevel 1 (
    echo ✗ v3-specific tests failed
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════════════════════
echo   ✓✓✓ ALL 65 TESTS PASSED ✓✓✓
echo ═══════════════════════════════════════════════════════════════
echo.
echo All 9 risks verified:
echo   ✓ Risk 1: GUC fast-path
echo   ✓ Risk 2: Safe trigger removal
echo   ✓ Risk 3: Streaming generator
echo   ✓ Risk 4: Watermark safety
echo   ✓ Risk 5: Migration locking
echo   ✓ Risk 6: Multi-tenant watermarks
echo   ✓ Risk 7: SECURITY DEFINER
echo   ✓ Risk 8: Complete pg_notify payload
echo   ✓ Risk 9: Concurrency & performance
echo.
echo See docs\CDC_V3_VERIFICATION_GUIDE.txt for details
echo.
pause
