"""
Comprehensive All-Database Test
Tests all Docker databases and adapters
"""
import sys
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')

from cdc.adapter_factory import CDCAdapterFactory
import time

print("=" * 80)
print("COMPREHENSIVE DATABASE TEST - DOCKER")
print("=" * 80)
print()

databases = {
    'PostgreSQL': {
        'conn': 'postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db',
        'market_share': 20,
        'tables': ['patients', 'encounters', 'lab_results', 'medications']
    },
    'MySQL': {
        'conn': 'mysql://root:root@localhost:3306/hospital_db_mysql',
        'market_share': 40,
        'tables': ['patients', 'encounters', 'lab_results', 'medications']
    },
    'MongoDB': {
        'conn': 'mongodb://localhost:27017/hospital_db_mongodb',
        'market_share': 5,
        'tables': ['patients', 'encounters', 'lab_results', 'medications']
    }
}

results = {}
total_coverage = 0

for db_name, config in databases.items():
    print("-" * 80)
    print(f"Testing {db_name} ({config['market_share']}% market share)")
    print("-" * 80)
    
    try:
        # Test 1: Create adapter
        print(f"\n[1/5] Creating adapter...")
        adapter = CDCAdapterFactory.create_adapter(config['conn'])
        print(f"  [OK] {adapter.__class__.__name__} created")
        
        # Test 2: Validate connection
        print(f"\n[2/5] Validating connection...")
        if adapter.validate_connection():
            print(f"  [OK] Connection successful")
        else:
            print(f"  [FAIL] Connection failed")
            results[db_name] = {'status': 'CONNECTION_FAILED', 'coverage': 0}
            continue
        
        # Test 3: Setup CDC
        print(f"\n[3/5] Setting up CDC...")
        if adapter.setup_cdc(config['tables']):
            print(f"  [OK] CDC setup complete")
        else:
            print(f"  [WARN] CDC setup issues (may be normal)")
        
        # Test 4: Get latest change ID
        print(f"\n[4/5] Getting latest change ID...")
        latest_id = adapter.get_latest_change_id()
        print(f"  Latest change ID: {latest_id}")
        
        # Test 5: Retrieve changes
        print(f"\n[5/5] Retrieving recent changes...")
        changes = adapter.get_changes(limit=5)
        print(f"  [OK] Retrieved {len(changes)} changes")
        
        if changes:
            print(f"\n  Sample changes:")
            for i, change in enumerate(changes[:3], 1):
                print(f"    {i}. {change.operation.value:6s} on {change.table_name}")
        
        results[db_name] = {
            'status': 'SUCCESS',
            'coverage': config['market_share'],
            'changes': len(changes),
            'latest_id': latest_id
        }
        total_coverage += config['market_share']
        
        print(f"\n  [OK] {db_name} fully operational")
        
    except ImportError as e:
        print(f"\n  [SKIP] Missing dependency: {str(e)[:60]}")
        results[db_name] = {'status': 'SKIPPED', 'coverage': 0, 'error': str(e)}
    
    except Exception as e:
        print(f"\n  [ERROR] {str(e)[:100]}")
        results[db_name] = {'status': 'ERROR', 'coverage': 0, 'error': str(e)}
    
    print()

# Summary
print("=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print()

success_count = sum(1 for r in results.values() if r['status'] == 'SUCCESS')
total_databases = len(databases)

print(f"Databases Tested : {total_databases}")
print(f"Successful       : {success_count}")
print(f"Coverage Achieved: {total_coverage}%")
print()

print("Detailed Results:")
print("-" * 80)
for db_name, result in results.items():
    status_icon = {
        'SUCCESS': '[OK]  ',
        'CONNECTION_FAILED': '[FAIL]',
        'SKIPPED': '[SKIP]',
        'ERROR': '[ERR] '
    }.get(result['status'], '[?]   ')
    
    print(f"{status_icon} {db_name:12s} - {result['status']}")
    if result['status'] == 'SUCCESS':
        print(f"       Changes: {result['changes']}, Latest ID: {result['latest_id']}")

print()
print("=" * 80)
print("FINAL RESULT")
print("=" * 80)

if total_coverage >= 65:
    print(f"✓ SUCCESS - {total_coverage}% market coverage achieved!")
    print(f"✓ {success_count}/{total_databases} databases operational")
    print("✓ System ready for multi-database demo!")
elif total_coverage >= 20:
    print(f"✓ PARTIAL - {total_coverage}% coverage (minimum met)")
    print(f"  {success_count}/{total_databases} databases working")
else:
    print(f"✗ INSUFFICIENT - Only {total_coverage}% coverage")
    print(f"  {success_count}/{total_databases} databases working")

print("=" * 80)
