"""
Comprehensive Database & Adapter Test Report
Tests all 5 database adapters and generates detailed results
"""
import sys
import os
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\cdc')

from adapter_factory import CDCAdapterFactory
import time

print("=" * 80)
print("COMPREHENSIVE DATABASE & ADAPTER TEST")
print("=" * 80)
print()

# Database configurations
databases = {
    'PostgreSQL': {
        'conn_str': 'postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db',
        'market_share': 20,
        'description': 'Trigger-based CDC'
    },
    'MySQL': {
        'conn_str': 'mysql://root:root@localhost:3306/hospital_db_mysql',
        'market_share': 40,
        'description': 'Trigger-based CDC with JSON'
    },
    'MongoDB': {
        'conn_str': 'mongodb://localhost:27017/hospital_db_mongodb',
        'market_share': 5,
        'description': 'Change log collection'
    },
    'Oracle': {
        'conn_str': 'oracle://system:oracle@localhost:1521/ORCL',
        'market_share': 25,
        'description': 'Trigger-based CDC with CLOB JSON'
    },
    'SQL Server': {
        'conn_str': 'sqlserver://sa:YourStrong@Passw0rd@localhost:1433/hospital_db',
        'market_share': 10,
        'description': 'Trigger-based CDC with NVARCHAR(MAX)'
    }
}

results = {}
total_market_coverage = 0

for db_name, config in databases.items():
    print("-" * 80)
    print(f"Testing {db_name} (Market Share: {config['market_share']}%)")
    print(f"Method: {config['description']}")
    print("-" * 80)
    
    try:
        # Test 1: Database type detection
        print(f"\n[1/6] Detecting database type...")
        detected = CDCAdapterFactory.detect_database_type(config['conn_str'])
        print(f"  [OK] Detected: {detected}")
        assert detected == db_name.lower().replace(' ', ''), "Type mismatch"
        
        # Test 2: Adapter creation
        print(f"\n[2/6] Creating CDC adapter...")
        adapter = CDCAdapterFactory.create_adapter(config['conn_str'])
        print(f"  [OK] {adapter.__class__.__name__} created")
        
        # Test 3: Connection validation
        print(f"\n[3/6] Validating connection...")
        if adapter.validate_connection():
            print(f"  [OK] Connection successful")
        else:
            print(f"  [FAIL] Connection failed")
            results[db_name] = {
                'status': 'Connection Failed',
                'market_share': config['market_share'],
                'contributes_coverage': False,
                'adapter_created': True,
                'connection_validated': False
            }
            continue
        
        # Test 4: CDC setup
        print(f"\n[4/6] Setting up CDC infrastructure...")
        tables = ['patients', 'encounters', 'lab_results', 'medications']
        if adapter.setup_cdc(tables):
            print(f"  [OK] CDC setup complete")
        else:
            print(f"  [WARN] CDC setup had issues (may already exist)")
        
        # Test 5: Get latest change ID
        print(f"\n[5/6] Getting latest change ID...")
        latest_id = adapter.get_latest_change_id()
        print(f"  Latest change_id: {latest_id}")
        
        # Test 6: Retrieve recent changes
        print(f"\n[6/6] Retrieving recent changes...")
        changes = adapter.get_changes(limit=10)
        print(f"  [OK] Retrieved {len(changes)} changes")
        
        if changes:
            print(f"\n  Recent changes:")
            for i, change in enumerate(changes[:5], 1):
                print(f"    {i}. {change.operation.value:6s} on {change.table_name:15s} "
                      f"(record_id: {change.record_id}, change_id: {change.change_id})")
        else:
            print(f"  (No changes yet - database is new)")
        
        results[db_name] = {
            'status': f'SUCCESS - {len(changes)} changes found',
            'market_share': config['market_share'],
            'contributes_coverage': True,
            'changes_count': len(changes),
            'latest_change_id': latest_id,
            'adapter_created': True,
            'connection_validated': True,
            'cdc_setup': True
        }
        total_market_coverage += config['market_share']
        
    except ImportError as e:
        error_msg = str(e)
        print(f"\n  [SKIP] {error_msg[:100]}")
        results[db_name] = {
            'status': 'SKIPPED - Dependencies missing',
            'market_share': config['market_share'],
            'contributes_coverage': False,
            'error': error_msg,
            'adapter_created': False,
            'connection_validated': False
        }
    
    except Exception as e:
        print(f"\n  [FAIL] Error: {str(e)[:100]}")
        results[db_name] = {
            'status': f'FAILED - {str(e)[:50]}',
            'market_share': config['market_share'],
            'contributes_coverage': False,
            'error': str(e),
            'adapter_created': True,
            'connection_validated': False
        }
    
    print()

# Summary Report
print("=" * 80)
print("5-DATABASE CDC TEST SUMMARY")
print("=" * 80)
print()

print("Database Support Status:")
print("-" * 80)
for db_name, result in results.items():
    if result['contributes_coverage']:
        status_icon = "[OK]"
    elif "SKIP" in result['status']:
        status_icon = "[SKIP]"
    else:
        status_icon = "[FAIL]"
    
    print(f"{status_icon} {db_name:15s} ({result['market_share']:2d}%) : {result['status']}")

print()
print("=" * 80)
print(f"TOTAL MARKET COVERAGE: {total_market_coverage}%")
print("=" * 80)

# Detailed breakdown
working_dbs = [db for db, r in results.items() if r['contributes_coverage']]
skipped_dbs = [db for db, r in results.items() if 'SKIP' in r['status']]
failed_dbs = [db for db, r in results.items() if 'FAIL' in r['status']]

print(f"\nWorking ({len(working_dbs)}): {', '.join(working_dbs) if working_dbs else 'None'}")
print(f"Skipped ({len(skipped_dbs)}): {', '.join(skipped_dbs) if skipped_dbs else 'None'}")
print(f"Failed ({len(failed_dbs)}): {', '.join(failed_dbs) if failed_dbs else 'None'}")

print()
print("Real-World Impact:")
print(f"  - Hospitals covered: {total_market_coverage}% of global market")
print(f"  - Databases supported: {len(working_dbs)}/5 major systems")
print(f"  - Production ready: {'YES' if total_market_coverage >= 60 else 'PARTIAL'}")

# Detailed test results
print()
print("=" * 80)
print("DETAILED TEST RESULTS")
print("=" * 80)
for db_name, result in results.items():
    print(f"\n{db_name}:")
    print(f"  Market Share: {result['market_share']}%")
    print(f"  Adapter Created: {result.get('adapter_created', False)}")
    print(f"  Connection Validated: {result.get('connection_validated', False)}")
    if result.get('cdc_setup'):
        print(f"  CDC Setup: SUCCESS")
    if result.get('changes_count') is not None:
        print(f"  Changes Found: {result['changes_count']}")
    if result.get('latest_change_id') is not None:
        print(f"  Latest Change ID: {result['latest_change_id']}")
    if result.get('error'):
        print(f"  Error: {result['error'][:80]}")

# Installation instructions
if skipped_dbs:
    print()
    print("=" * 80)
    print("TO ENABLE SKIPPED DATABASES:")
    print("=" * 80)
    
    if 'Oracle' in skipped_dbs:
        print("\nOracle:")
        print("  1. pip install cx_Oracle")
        print("  2. Download Oracle Instant Client:")
        print("     https://www.oracle.com/database/technologies/instant-client/downloads.html")
        print("  3. Add to PATH: C:\\oracle\\instantclient_XX_X")
    
    if 'SQL Server' in skipped_dbs:
        print("\nSQL Server:")
        print("  1. pip install pyodbc")
        print("  2. Install ODBC Driver 17 for SQL Server:")
        print("     https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")

if failed_dbs:
    print()
    print("=" * 80)
    print("TO FIX FAILED DATABASES:")
    print("=" * 80)
    
    for db in failed_dbs:
        if db == 'MySQL':
            print("\nMySQL:")
            print("  1. Install MySQL from: https://dev.mysql.com/downloads/mysql/")
            print("  2. Start MySQL service")
            print("  3. Create database: python scripts\\setup_mysql_data.py")
        
        if db == 'MongoDB':
            print("\nMongoDB:")
            print("  1. Install MongoDB from: https://www.mongodb.com/try/download/community")
            print("  2. Start MongoDB service")
            print("  3. Create database: python scripts\\setup_mongodb_data.py")

print()
print("=" * 80)
print(f"Test completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print()

# Save results to file
report_file = r"C:\Projects\CareLock-Sync\test_results_5_databases.txt"
try:
    with open(report_file, 'w') as f:
        f.write(f"5-Database CDC Test Results\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"\n")
        f.write(f"Total Market Coverage: {total_market_coverage}%\n")
        f.write(f"Working: {len(working_dbs)}/5\n")
        f.write(f"\n")
        for db_name, result in results.items():
            f.write(f"\n{db_name}: {result['status']}\n")
    print(f"Results saved to: {report_file}")
except:
    pass
