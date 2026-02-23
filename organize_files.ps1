# CareLock Sync - File Organization Script
# Moves all unnecessary files from root to appropriate folders

Write-Host ("="*70)
Write-Host "  CareLock Sync - File Organization"
Write-Host ("="*70)
Write-Host ""

$moved = 0
$failed = 0

# Function to move file safely
function Move-FileSafely {
    param($Source, $Destination)
    
    if (Test-Path $Source) {
        try {
            Move-Item -Path $Source -Destination $Destination -Force
            Write-Host "  OK Moved: $Source -> $Destination"
            return $true
        } catch {
            Write-Host "  X Failed: $Source - $_" -ForegroundColor Red
            return $false
        }
    } else {
        Write-Host "  - Skipped: $Source (not found)"
        return $null
    }
}

# 1. Move Reports to docs/reports/
Write-Host "Moving reports to docs/reports/..."
$reports = @(
    "COMPREHENSIVE_IMPLEMENTATION_ANALYSIS.txt",
    "FINAL_SUCCESS_REPORT.txt",
    "PROJECT_COMPLETION_REPORT.txt",
    "FIX_TEST_FAILURES.txt",
    "encryption_test_results.txt",
    "verification_results.txt",
    "test_output.txt"
)

foreach ($file in $reports) {
    $result = Move-FileSafely $file "docs\reports\$file"
    if ($result -eq $true) { $script:moved++ }
    elseif ($result -eq $false) { $script:failed++ }
}

# 2. Move Security Documentation to docs/security/
Write-Host ""
Write-Host "Moving security documentation to docs/security/..."
$security_docs = @(
    "INCIDENT_RESPONSE_PLAN.md"
)

foreach ($file in $security_docs) {
    $result = Move-FileSafely $file "docs\security\$file"
    if ($result -eq $true) { $script:moved++ }
    elseif ($result -eq $false) { $script:failed++ }
}

# 3. Move Setup Scripts to scripts/
Write-Host ""
Write-Host "Moving setup scripts to scripts/..."
$setup_scripts = @(
    "setup.ps1",
    "setup_complete.ps1",
    "check_install.ps1",
    "check_env.py"
)

foreach ($file in $setup_scripts) {
    $result = Move-FileSafely $file "scripts\$file"
    if ($result -eq $true) { $script:moved++ }
    elseif ($result -eq $false) { $script:failed++ }
}

# 4. Move Test Scripts to scripts/testing/
Write-Host ""
Write-Host "Moving test scripts to scripts/testing/..."
$test_scripts = @(
    "RUN_ALL_CDC_TESTS.bat",
    "RUN_CDC_V3_TESTS.bat",
    "RUN_SPRINT4_TEST.bat",
    "CLEANUP_NOW.bat",
    "_cleanup_old_files.bat"
)

foreach ($file in $test_scripts) {
    $result = Move-FileSafely $file "scripts\testing\$file"
    if ($result -eq $true) { $script:moved++ }
    elseif ($result -eq $false) { $script:failed++ }
}

# 5. Move Temporary Files to scripts/temp/
Write-Host ""
Write-Host "Moving temporary files to scripts/temp/..."
$temp_files = @(
    "tmp_check.py",
    "tmp_compose.py",
    "tmp_d2.py",
    "tmp_db3.py",
    "tmp_dbcheck.py",
    "tmp_docker.py",
    "tmp_scan.py",
    "t.py",
    "migrate_cdc_to_v3.py",
    "diagnose_embed.py"
)

foreach ($file in $temp_files) {
    $result = Move-FileSafely $file "scripts\temp\$file"
    if ($result -eq $true) { $script:moved++ }
    elseif ($result -eq $false) { $script:failed++ }
}

# 6. Move Log Files to logs/
Write-Host ""
Write-Host "Moving log files to logs/..."
$log_files = @(
    "out.txt",
    "err.txt",
    "tmp_out.txt",
    "tmp_err.txt",
    "tmp_stdout.txt",
    "tmp_stderr.txt"
)

foreach ($file in $log_files) {
    $result = Move-FileSafely $file "logs\$file"
    if ($result -eq $true) { $script:moved++ }
    elseif ($result -eq $false) { $script:failed++ }
}

# 7. Move Database Files to databases/
Write-Host ""
Write-Host "Moving database files to databases/..."
$db_files = @(
    "carelock_audit.db"
)

foreach ($file in $db_files) {
    $result = Move-FileSafely $file "databases\$file"
    if ($result -eq $true) { $script:moved++ }
    elseif ($result -eq $false) { $script:failed++ }
}

# Summary
Write-Host ""
Write-Host ("="*70)
Write-Host "  ORGANIZATION COMPLETE"
Write-Host ("="*70)
Write-Host ""
Write-Host "Files moved: $moved"
Write-Host "Failures: $failed"
Write-Host ""

# Show remaining files in root
Write-Host "Remaining files in root directory:"
$remaining = Get-ChildItem -Path . -File | Where-Object { 
    $_.Name -notlike ".*" -and 
    $_.Name -ne "organize_files.ps1"
}

if ($remaining.Count -gt 0) {
    foreach ($file in $remaining) {
        Write-Host "  - $($file.Name)"
    }
} else {
    Write-Host "  OK Root directory is clean!"
}

Write-Host ""
Write-Host "Essential files kept in root:"
Write-Host "  OK .env (configuration)"
Write-Host "  OK .gitignore (git)"
Write-Host "  OK README.md (documentation)"
Write-Host "  OK SETUP.md (setup guide)"
Write-Host "  OK SETUP_GUIDE.md (detailed guide)"
Write-Host "  OK docker-compose.yml (docker)"
Write-Host "  OK pytest.ini (testing config)"
Write-Host "  OK run_secure_server.py (server launcher)"
Write-Host ""
Write-Host ("="*70)
Write-Host "  Organization complete!"
Write-Host ("="*70)
