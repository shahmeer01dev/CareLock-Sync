"""
Multi-Database CDC Test
Tests CDC and ETL across PostgreSQL, MySQL, and MongoDB

Requirements:
- PostgreSQL on localhost:5432 with hospital_db
- MySQL on localhost:3306 with hospital_db_mysql  
- MongoDB on localhost:27017 with hospital_db_mongodb
"""
import sys
import os

# Add paths
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\cdc')

from adapter_factory import CDCAdapterFactory
import time

print("=" * 80)
print("MULTI-DATABASE CDC & ETL TEST")
print("=" * 80)
print()

# Database connection strings
databases = {
    'PostgreSQL': 'postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db',
    'MySQL': 'mysql://root:root@localhost:3306/hospital_db_mysql',
    'MongoDB': 'mongodb://localhost:27017/hospital_db_mongodb'
}

results = {}

for db_name, conn_str in databases.items():
    print("-" * 80)
    print(f"Testing {db_name}")
    print("-" * 80)
    
    try:
        # Test 1: Create adapter
        print(f"\n[1/5] Creating {db_name} CDC adapter...")
        adapter = CDCAdapterFactory.create_adapter(conn_str)
        detected_type = adapter.get_database_type()
        print(f"  [OK] Adapter created - Type: {detected_type}")
        
        # Test 2: Validate connection
        print(f"\n[2/5] Validating connection...")
        if adapter.validate_connection():
            print(f"  [OK] Connection valid")
        else:
            print(f"  [FAIL] Connection failed")
            results[db_name] = "Connection Failed"
            continue
        
        # Test 3: Setup CDC
        print(f"\n[3/5] Setting up CDC...")
        tables = ['patients', 'encounters', 'lab_results', 'medications']
        if db_name == 'MongoDB':
            tables = ['patients', 'encounters', 'lab_results', 'medications']
        
        if adapter.setup_cdc(tables):
            print(f"  [OK] CDC setup complete")
        else:
            print(f"  [WARN] CDC setup had issues")
        
        # Test 4: Get latest change ID
        print(f"\n[4/5] Getting latest change ID...")
        latest_id = adapter.get_latest_change_id()
        print(f"  Latest change ID: {latest_id}")
        
        # Test 5: Get recent changes
        print(f"\n[5/5] Retrieving recent changes...")
        changes = adapter.get_changes(limit=5)
        print(f"  [OK] Retrieved {len(changes)} recent changes")
        
        if changes:
            print(f"\n  Sample changes:")
            for i, change in enumerate(changes[:3], 1):
                print(f"    {i}. {change.operation.value} on {change.table_name} (ID: {change.record_id})")
        
        results[db_name] = f"Success - {len(changes)} changes found"
        
    except ImportError as e:
        print(f"  [SKIP] {e}")
        results[db_name] = f"Skipped - Missing dependencies"
    except Exception as e:
        print(f"  [FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        results[db_name] = f"Failed - {str(e)[:50]}"
    
    print()

# Summary
print("=" * 80)
print("MULTI-DATABASE TEST SUMMARY")
print("=" * 80)

for db_name, result in results.items():
    status = "[OK]" if "Success" in result else "[FAIL]" if "Failed" in result else "[SKIP]"
    print(f"{status} {db_name:15s} : {result}")

# Calculate coverage
supported = sum(1 for r in results.values() if "Success" in r)
total = len(results)
coverage_pct = (supported / total) * 100 if total > 0 else 0

print(f"\nDatabase Coverage: {supported}/{total} ({coverage_pct:.0f}%)")

# Map to real-world distribution
real_world = {
    'PostgreSQL': 20,
    'MySQL': 40,
    'MongoDB': 5,
}

covered_percentage = sum(
    real_world.get(db, 0) 
    for db, result in results.items() 
    if "Success" in result
)

print(f"Real-World Hospital Coverage: {covered_percentage}%")
print("  (Based on: MySQL 40%, PostgreSQL 20%, MongoDB 5%)")

print("\n" + "=" * 80)
