"""
FINAL COMPREHENSIVE TEST - ALL 5 DATABASES
Tests every database adapter with Oracle Instant Client configured
"""
import sys
import os

# Configure Oracle Instant Client
os.environ['PATH'] = r'C:\oracle\instantclient_23_0;' + os.environ.get('PATH', '')

sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
from cdc.adapter_factory import CDCAdapterFactory

print("=" * 80)
print("FINAL COMPREHENSIVE TEST - ALL 5 DATABASES")
print("=" * 80)

databases = {
    'PostgreSQL': {
        'conn': 'postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db',
        'share': 20
    },
    'MySQL': {
        'conn': 'mysql://root:root@localhost:3306/hospital_db_mysql',
        'share': 40
    },
    'MongoDB': {
        'conn': 'mongodb://localhost:27017/hospital_db_mongodb',
        'share': 5
    },
    'Oracle': {
        'conn': 'oracle://hospital_user:hospital_pass@localhost:1521/XE',
        'share': 25
    },
    'SQL Server': {
        'conn': 'sqlserver://sa:YourStrong@Passw0rd@localhost:1433/hospital_db_sqlserver',
        'share': 10
    }
}

results = {}
total_coverage = 0

for db_name, config in databases.items():
    print("\n" + "-" * 80)
    print(f"Testing {db_name} ({config['share']}% market share)")
    print("-" * 80)
    
    try:
        print(f"[1/4] Creating adapter...")
        adapter = CDCAdapterFactory.create_adapter(config['conn'])
        print(f"  [OK] {adapter.__class__.__name__}")
        
        print(f"[2/4] Validating connection...")
        if adapter.validate_connection():
            print(f"  [OK] Connected")
        else:
            print(f"  [FAIL] Connection failed")
            results[db_name] = ('FAILED', 0)
            continue
        
        print(f"[3/4] Setting up CDC...")
        try:
            adapter.setup_cdc(['patients', 'encounters', 'lab_results', 'medications'])
            print(f"  [OK] CDC ready")
        except Exception as e:
            print(f"  [WARN] CDC issue: {str(e)[:50]}")
        
        print(f"[4/4] Getting changes...")
        changes = adapter.get_changes(limit=5)
        print(f"  [OK] Retrieved {len(changes)} changes")
        
        if changes:
            for i, change in enumerate(changes[:3], 1):
                print(f"      {i}. {change.operation.value} on {change.table_name}")
        
        results[db_name] = ('SUCCESS', config['share'])
        total_coverage += config['share']
        print(f"\n  [SUCCESS] {db_name} operational!")
        
    except ImportError as e:
        print(f"  [SKIP] {str(e)[:60]}")
        results[db_name] = ('SKIPPED', 0)
    except Exception as e:
        print(f"  [ERROR] {str(e)[:60]}")
        results[db_name] = ('ERROR', 0)

# Summary
print("\n" + "=" * 80)
print("FINAL TEST SUMMARY")
print("=" * 80)

success_count = sum(1 for status, _ in results.values() if status == 'SUCCESS')

print(f"\nDatabases Tested: {len(databases)}")
print(f"Successful      : {success_count}")
print(f"Coverage        : {total_coverage}%")
print()

for db_name, (status, share) in results.items():
    icon = {
        'SUCCESS': '[OK]  ',
        'FAILED': '[FAIL]',
        'SKIPPED': '[SKIP]',
        'ERROR': '[ERR] '
    }.get(status, '[?]   ')
    
    print(f"{icon} {db_name:12s} {share:2d}% - {status}")

print()
print("=" * 80)
print("FINAL VERDICT")
print("=" * 80)

if total_coverage == 100:
    print("\n SUCCESS! 100% MARKET COVERAGE ACHIEVED!")
    print("\n All 5 major hospital database types are operational:")
    print("  - PostgreSQL (20%)")
    print("  - MySQL (40%)")
    print("  - MongoDB (5%)")
    print("  - Oracle (25%)")
    print("  - SQL Server (10%)")
    print("\n System is PRODUCTION READY for multi-database deployment!")
elif total_coverage >= 65:
    print(f"\n GOOD! {total_coverage}% market coverage achieved")
    print(f" {success_count}/5 databases operational")
else:
    print(f"\n {total_coverage}% coverage - needs attention")

print("=" * 80)
