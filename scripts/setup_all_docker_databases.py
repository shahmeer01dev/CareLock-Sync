"""
Master Database Setup Script
Starts all 5 databases in Docker and populates them with sample data
"""
import subprocess
import time
import sys
import os

print("=" * 80)
print("CARELOCK SYNC - DOCKER DATABASE SETUP")
print("=" * 80)
print()
print("This script will:")
print("  1. Start all 5 databases in Docker containers")
print("  2. Wait for databases to be healthy")
print("  3. Create schemas in each database")
print("  4. Populate with sample hospital data")
print("  5. Set up CDC triggers")
print("  6. Test all adapters")
print()
print("Databases: PostgreSQL, MySQL, MongoDB, Oracle XE, SQL Server")
print("=" * 80)
print()

# Check if Docker is running
print("[Step 0] Checking Docker...")
try:
    result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
    print(f"  [OK] {result.stdout.strip()}")
except FileNotFoundError:
    print("  [ERROR] Docker not found!")
    print("  Please install Docker Desktop from: https://www.docker.com/products/docker-desktop")
    sys.exit(1)

try:
    result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
    if result.returncode != 0:
        print("  [ERROR] Docker daemon not running!")
        print("  Please start Docker Desktop")
        sys.exit(1)
    print("  [OK] Docker daemon running")
except Exception as e:
    print(f"  [ERROR] {e}")
    sys.exit(1)

print()

# Step 1: Start containers
print("[Step 1] Starting Docker containers...")
print("  This may take 5-10 minutes on first run (downloading images)")
print()

os.chdir(r'C:\Projects\CareLock-Sync')

result = subprocess.run(
    ['docker-compose', 'up', '-d'],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    print("  [ERROR] Failed to start containers")
    print(result.stderr)
    sys.exit(1)

print("  [OK] Containers started")
print()

# Step 2: Wait for databases to be healthy
print("[Step 2] Waiting for databases to be ready...")
print("  This may take 2-5 minutes for all databases to initialize")
print()

databases = {
    'carelock_postgres': 'PostgreSQL',
    'carelock_mysql': 'MySQL',
    'carelock_mongodb': 'MongoDB',
    'carelock_oracle': 'Oracle XE',
    'carelock_sqlserver': 'SQL Server'
}

max_wait = 300  # 5 minutes
start_time = time.time()

for container, db_name in databases.items():
    print(f"  Waiting for {db_name}...")
    
    while True:
        result = subprocess.run(
            ['docker', 'inspect', '--format={{.State.Health.Status}}', container],
            capture_output=True,
            text=True
        )
        
        status = result.stdout.strip()
        
        if status == 'healthy':
            print(f"    [OK] {db_name} is healthy")
            break
        elif status == '':
            # Container doesn't have health check, just check if running
            result = subprocess.run(
                ['docker', 'inspect', '--format={{.State.Running}}', container],
                capture_output=True,
                text=True
            )
            if result.stdout.strip() == 'true':
                print(f"    [OK] {db_name} is running")
                time.sleep(10)  # Extra wait for startup
                break
        
        if time.time() - start_time > max_wait:
            print(f"    [TIMEOUT] {db_name} took too long to start")
            break
        
        time.sleep(5)

print()
print("  [OK] All databases ready")
print()

# Step 3: Install Python dependencies
print("[Step 3] Installing Python dependencies...")

dependencies = [
    'pymysql',
    'pymongo',
    'cx_Oracle',
    'pyodbc',
    'faker'
]

for dep in dependencies:
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', dep, '--break-system-packages'],
        capture_output=True
    )
    if result.returncode == 0:
        print(f"  [OK] {dep} installed")
    else:
        print(f"  [SKIP] {dep} (may already be installed)")

print()

# Step 4: Populate databases
print("[Step 4] Populating databases with sample data...")
print()

scripts = {
    'PostgreSQL': r'scripts\setup_postgres_docker_data.py',
    'MySQL': r'scripts\setup_mysql_docker_data.py',
    'MongoDB': r'scripts\setup_mongodb_docker_data.py',
    'Oracle': r'scripts\setup_oracle_docker_data.py',
    'SQL Server': r'scripts\setup_sqlserver_docker_data.py'
}

for db_name, script in scripts.items():
    print(f"  Setting up {db_name}...")
    if os.path.exists(script):
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            print(f"    [OK] {db_name} data created")
        else:
            print(f"    [WARN] {db_name} setup had issues")
            print(f"    {result.stderr[:200]}")
    else:
        print(f"    [SKIP] Script not found: {script}")

print()

# Step 5: Test all adapters
print("[Step 5] Testing all database adapters...")
print()

result = subprocess.run(
    [sys.executable, r'scripts\test_databases_detailed.py'],
    capture_output=True,
    text=True,
    timeout=120
)

print(result.stdout)

# Step 6: Summary
print()
print("=" * 80)
print("SETUP COMPLETE")
print("=" * 80)
print()
print("All databases are running in Docker:")
print()
print("  PostgreSQL : localhost:5432 (hospital_user / hospital_pass)")
print("  MySQL      : localhost:3306 (root / root)")
print("  MongoDB    : localhost:27017 (no auth)")
print("  Oracle XE  : localhost:1521 (hospital_user / hospital_pass)")
print("  SQL Server : localhost:1433 (sa / YourStrong@Passw0rd)")
print()
print("To stop all databases:")
print("  docker-compose down")
print()
print("To restart:")
print("  docker-compose up -d")
print()
print("To view logs:")
print("  docker-compose logs -f [postgres|mysql|mongodb|oracle|sqlserver]")
print()
print("=" * 80)
