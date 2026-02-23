@echo off
echo.
echo ═══════════════════════════════════════════════════════════
echo   Cleaning Up Old Test Files
echo ═══════════════════════════════════════════════════════════
echo.

cd /d C:\Projects\CareLock-Sync

if not exist "_archive_old_tests" mkdir "_archive_old_tests"

echo Moving old debug/test files...
move /Y debug_*.py "_archive_old_tests\" 2>nul
move /Y diag_*.py "_archive_old_tests\" 2>nul
move /Y test_*.py "_archive_old_tests\" 2>nul
move /Y run_*.py "_archive_old_tests\" 2>nul
move /Y *_test.py "_archive_old_tests\" 2>nul
move /Y *_check*.py "_archive_old_tests\" 2>nul
move /Y preload_*.py "_archive_old_tests\" 2>nul
move /Y rebuild_*.py "_archive_old_tests\" 2>nul
move /Y reload_*.py "_archive_old_tests\" 2>nul
move /Y check_*.py "_archive_old_tests\" 2>nul

echo Moving log files...
move /Y *.log "_archive_old_tests\" 2>nul
move /Y *_err.txt "_archive_old_tests\" 2>nul
move /Y *_out*.txt "_archive_old_tests\" 2>nul
move /Y test_*.txt "_archive_old_tests\" 2>nul
move /Y tmp_*.txt "_archive_old_tests\" 2>nul
move /Y rag_*.txt "_archive_old_tests\" 2>nul

echo Moving old run scripts...
move /Y run_test.bat "_archive_old_tests\" 2>nul
move /Y run_test.ps1 "_archive_old_tests\" 2>nul

echo.
echo ✓ Cleanup complete!
echo.
echo Old files archived to: _archive_old_tests\
echo.

echo Remaining files in root directory:
dir /b /a-d | findstr /v /i "\.git .env .gitignore docker-compose.yml README.md SETUP RUN_SPRINT4_TEST.bat _cleanup_old_files.bat _archive_old_tests"

echo.
echo ═══════════════════════════════════════════════════════════
echo   Root directory is now clean!
echo ═══════════════════════════════════════════════════════════
echo.
pause
