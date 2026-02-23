@echo off
echo Cleaning up old test files...
cd /d C:\Projects\CareLock-Sync
move debug_*.py _archive_old_tests\ >nul 2>&1
move diag_*.py _archive_old_tests\ >nul 2>&1
move test_*.py _archive_old_tests\ >nul 2>&1
move run_*.py _archive_old_tests\ >nul 2>&1
move *_test.py _archive_old_tests\ >nul 2>&1
move preload_*.py _archive_old_tests\ >nul 2>&1
move rebuild_*.py _archive_old_tests\ >nul 2>&1
move reload_*.py _archive_old_tests\ >nul 2>&1
move *_check_*.py _archive_old_tests\ >nul 2>&1
move *.txt _archive_old_tests\ >nul 2>&1
move *.log _archive_old_tests\ >nul 2>&1
move run_test.* _archive_old_tests\ >nul 2>&1
echo.
echo ✓ Old files archived to _archive_old_tests folder
echo.
echo Project root is now clean!
pause
