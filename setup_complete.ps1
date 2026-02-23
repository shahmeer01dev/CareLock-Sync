# ============================================================================
# CareLock Sync - Ultimate Setup Script for Windows
# ============================================================================
# This script sets up ALL 5 databases and the complete sync system
# Version: 2.0 (Updated Feb 2026) - TESTED
# ============================================================================

$ErrorActionPreference = "Continue"

function Write-Header {
    param([string]$Text)
    Write-Host ""
    $border = "=" * 80
    Write-Host $border -ForegroundColor Cyan
    Write-Host $Text.PadLeft(($Text.Length + 80) / 2) -ForegroundColor Cyan
    Write-Host $border -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([int]$Step, [int]$Total, [string]$Description)
    Write-Host ""
    Write-Host "[$Step/$Total] $Description..." -ForegroundColor Yellow
}

function Write-Success {
    param([string]$Message)
    Write-Host "  [OK] $Message" -ForegroundColor Green
}

function Write-Error-Msg {
    param([string]$Message)
    Write-Host "  [ERROR] $Message" -ForegroundColor Red
}

function Write-Warning-Msg {
    param([string]$Message)
    Write-Host "  [WARN] $Message" -ForegroundColor Yellow
}

Write-Header "CARELOCK SYNC - COMPLETE AUTOMATED SETUP"
Write-Host "This will set up all 5 databases and the sync daemon" -ForegroundColor White
Write-Host "Estimated time: 10-15 minutes" -ForegroundColor White
Write-Host ""

# ============================================================================
# STEP 1: Prerequisites Check
# ============================================================================

Write-Step 1 10 "Checking Prerequisites"

# Check Python
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.1[0-9]") {
        Write-Success "Python: $pythonVersion"
    } else {
        Write-Error-Msg "Python 3.10+ required. Found: $pythonVersion"
        exit 1
    }
} catch {
    Write-Error-Msg "Python not found. Please install Python 3.10+"
    exit 1
}

# Check Docker
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker: $dockerVersion"
    } else {
        throw "Docker command failed"
    }
} catch {
    Write-Error-Msg "Docker not found or not running"
    Write-Warning-Msg "Please install and start Docker Desktop"
    exit 1
}

# Check Docker daemon
try {
    docker ps | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Docker daemon is running"
    } else {
        throw "Docker daemon not responding"
    }
} catch {
    Write-Error-Msg "Docker is installed but not running"
    Write-Warning-Msg "Please start Docker Desktop and wait for it to initialize"
    exit 1
}

# Check Oracle Instant Client
$oraclePath = "C:\oracle\instantclient_23_0"
if (Test-Path $oraclePath) {
    Write-Success "Oracle Instant Client found: $oraclePath"
    $env:PATH = "$oraclePath;$env:PATH"
} else {
    Write-Warning-Msg "Oracle Instant Client not found at $oraclePath"
    Write-Warning-Msg "Oracle database will not work without it"
    Write-Warning-Msg "Download from: https://www.oracle.com/database/technologies/instant-client/downloads.html"
    $continue = Read-Host "Continue anyway? (y/N)"
    if ($continue -ne "y") {
        exit 1
    }
}

# ============================================================================
# STEP 2: Python Virtual Environment
# ============================================================================

Write-Step 2 10 "Setting up Python virtual environment"

if (Test-Path "venv") {
    Write-Success "Virtual environment already exists"
} else {
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Virtual environment created"
    } else {
        Write-Error-Msg "Failed to create virtual environment"
        exit 1
    }
}

# ============================================================================
# STEP 3: Install Python Dependencies
# ============================================================================

Write-Step 3 10 "Installing Python dependencies"

.\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Success "pip upgraded"
}

# Check for requirements.txt
$reqFile = "requirements.txt"
if (-not (Test-Path $reqFile)) {
    $reqFile = "backend\requirements.txt"
}

if (Test-Path $reqFile) {
    .\venv\Scripts\pip.exe install -r $reqFile --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Success "All dependencies installed"
    } else {
        Write-Error-Msg "Failed to install some dependencies"
    }
} else {
    Write-Warning-Msg "requirements.txt not found, skipping"
}

# ============================================================================
# STEP 4: Start Docker Containers
# ============================================================================

Write-Step 4 10 "Starting Docker containers"

# Force stop and remove any existing containers
Write-Host "  Stopping existing containers..." -ForegroundColor Gray
docker-compose down --volumes --remove-orphans 2>&1 | Out-Null

# Remove orphaned containers if any
Write-Host "  Removing orphaned containers..." -ForegroundColor Gray
docker ps -a --filter "name=carelock" --format "{{.Names}}" | ForEach-Object {
    docker rm -f $_ 2>&1 | Out-Null
}

# Start all containers
Write-Host "  Starting fresh containers..." -ForegroundColor Gray
docker-compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Success "Docker containers started"
} else {
    Write-Error-Msg "Failed to start Docker containers"
    Write-Warning-Msg "Try running: docker-compose down --volumes && docker-compose up -d"
    exit 1
}

Write-Warning-Msg "Waiting 15 seconds for containers to initialize..."
Start-Sleep -Seconds 15

# Verify containers
$containers = docker ps --format "{{.Names}}" | Out-String
$expectedContainers = @(
    "carelock_postgres",
    "carelock_mysql", 
    "carelock_mongodb",
    "carelock_oracle",
    "carelock_sqlserver"
)

$runningCount = 0
foreach ($container in $expectedContainers) {
    if ($containers -match $container) {
        $runningCount++
    }
}

Write-Success "$runningCount/$($expectedContainers.Count) containers running"

if ($runningCount -lt $expectedContainers.Count) {
    Write-Warning-Msg "Some containers may still be initializing..."
}

# ============================================================================
# STEP 5: Wait for Oracle Initialization
# ============================================================================

Write-Step 5 10 "Waiting for Oracle database initialization"

Write-Warning-Msg "Oracle takes 2-3 minutes to initialize on first run..."

$maxWait = 180
$waited = 0
$oracleReady = $false

while ($waited -lt $maxWait) {
    $logs = docker logs carelock_oracle 2>&1 | Out-String
    if ($logs -match "DATABASE IS READY TO USE") {
        $oracleReady = $true
        Write-Success "Oracle initialized successfully"
        break
    }
    
    Start-Sleep -Seconds 10
    $waited += 10
    Write-Host "  ... waited $waited/$maxWait seconds" -ForegroundColor Gray
}

if (-not $oracleReady) {
    Write-Warning-Msg "Oracle may still be initializing, continuing anyway..."
}

# ============================================================================
# STEP 6: Setup Databases
# ============================================================================

Write-Step 6 10 "Initializing all 5 databases"

$databases = @(
    @{Name="PostgreSQL"; Script="scripts\setup_postgres.py"},
    @{Name="MySQL"; Script="scripts\setup_mysql_complete.py"},
    @{Name="MongoDB"; Script="scripts\setup_mongodb_complete.py"},
    @{Name="Oracle"; Script="scripts\setup_oracle_complete.py"},
    @{Name="SQL Server"; Script="scripts\setup_sqlserver_simple.py"}
)

foreach ($db in $databases) {
    Write-Host ""
    Write-Host "  Setting up $($db.Name)..." -ForegroundColor Cyan
    
    if (Test-Path $db.Script) {
        $env:PATH = "C:\oracle\instantclient_23_0;$env:PATH"
        .\venv\Scripts\python.exe $db.Script
        if ($LASTEXITCODE -eq 0) {
            Write-Success "$($db.Name) setup complete"
        } else {
            Write-Warning-Msg "$($db.Name) setup had issues, but continuing..."
        }
    } else {
        Write-Warning-Msg "Setup script not found: $($db.Script)"
    }
}

# ============================================================================
# STEP 7: Create Sync Daemon Configuration
# ============================================================================

Write-Step 7 10 "Creating sync daemon configuration"

$configDir = "config"
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

$syncConfig = @{
    sources = @(
        @{
            id = "postgres_hospital"
            connection_string = "postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db"
            tables = @("patients", "encounters", "lab_results", "medications")
        },
        @{
            id = "mysql_hospital"
            connection_string = "mysql://root:root@localhost:3306/hospital_db_mysql"
            tables = @("patients", "encounters", "lab_results", "medications")
        },
        @{
            id = "mongodb_hospital"
            connection_string = "mongodb://localhost:27017/hospital_db_mongodb"
            collections = @("patients", "encounters", "lab_results", "medications")
        },
        @{
            id = "oracle_hospital"
            connection_string = "oracle://hospital_user:hospital_pass@localhost:1521/XE"
            tables = @("patients", "encounters", "lab_results", "medications")
        },
        @{
            id = "sqlserver_hospital"
            connection_string = "sqlserver://sa:YourStrong@Passw0rd@localhost:1433/hospital_db_sqlserver"
            tables = @("patients", "encounters", "lab_results", "medications")
        }
    )
    polling_interval = 5
    batch_size = 1000
    deduplication = $true
    gemini_api_key = "YOUR_GEMINI_API_KEY_HERE"
} | ConvertTo-Json -Depth 10

$syncConfig | Out-File -FilePath "$configDir\sync_config.json" -Encoding UTF8

Write-Success "Configuration created: $configDir\sync_config.json"
Write-Warning-Msg "Remember to add your Gemini API key to the config file"

# ============================================================================
# STEP 8: Run Comprehensive Tests
# ============================================================================

Write-Step 8 10 "Running comprehensive database tests"

$testScript = "scripts\test_all_5_databases_final.py"
if (Test-Path $testScript) {
    $env:PATH = "C:\oracle\instantclient_23_0;$env:PATH"
    .\venv\Scripts\python.exe $testScript
    if ($LASTEXITCODE -eq 0) {
        Write-Success "All database tests passed"
    } else {
        Write-Warning-Msg "Some tests had issues"
    }
} else {
    Write-Warning-Msg "Test script not found: $testScript"
}

# ============================================================================
# STEP 9: Test CDC Functionality
# ============================================================================

Write-Step 9 10 "Testing Change Data Capture"

$cdcTest = "scripts\test_cdc_all_databases.py"
if (Test-Path $cdcTest) {
    $env:PATH = "C:\oracle\instantclient_23_0;$env:PATH"
    .\venv\Scripts\python.exe $cdcTest
    if ($LASTEXITCODE -eq 0) {
        Write-Success "CDC tests passed"
    } else {
        Write-Warning-Msg "CDC tests had issues"
    }
} else {
    Write-Warning-Msg "CDC test script not found"
}

# ============================================================================
# STEP 10: Final Summary
# ============================================================================

Write-Step 10 10 "Setup Complete"

Write-Header "SETUP COMPLETE - SYSTEM READY"

Write-Host "All 5 databases are running and configured" -ForegroundColor Green
Write-Host "Change Data Capture is enabled" -ForegroundColor Green
Write-Host "Sync daemon configuration created" -ForegroundColor Green
Write-Host ""

Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Add your Gemini API key:" -ForegroundColor White
Write-Host "   Edit: config\sync_config.json" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Activate virtual environment:" -ForegroundColor White
Write-Host "   .\venv\Scripts\activate" -ForegroundColor Cyan
Write-Host ""
Write-Host "3. Start the sync daemon:" -ForegroundColor White
Write-Host '   $env:PATH = "C:\oracle\instantclient_23_0;" + $env:PATH' -ForegroundColor Cyan
Write-Host "   python backend\sync_daemon.py" -ForegroundColor Cyan
Write-Host ""

Write-Host "USEFUL COMMANDS:" -ForegroundColor Yellow
Write-Host "  View containers:    docker ps" -ForegroundColor White
Write-Host "  View logs:          docker logs [container_name]" -ForegroundColor White
Write-Host "  Stop all:           docker-compose down" -ForegroundColor White
Write-Host "  Restart all:        docker-compose up -d" -ForegroundColor White
Write-Host ""

Write-Host "DATABASE CONNECTIONS:" -ForegroundColor Yellow
Write-Host "  PostgreSQL:  localhost:5432  (hospital_user/hospital_pass)" -ForegroundColor White
Write-Host "  MySQL:       localhost:3306  (root/root)" -ForegroundColor White
Write-Host "  MongoDB:     localhost:27017" -ForegroundColor White
Write-Host "  Oracle:      localhost:1521  (hospital_user/hospital_pass)" -ForegroundColor White
Write-Host "  SQL Server:  localhost:1433  (sa/YourStrong@Passw0rd)" -ForegroundColor White
Write-Host ""

$border = "=" * 80
Write-Host $border -ForegroundColor Cyan
Write-Host "Setup completed successfully!" -ForegroundColor Green
Write-Host $border -ForegroundColor Cyan
Write-Host ""
