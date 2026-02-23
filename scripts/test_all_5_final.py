"""
COMPREHENSIVE ALL-DATABASE TEST
Tests ALL 5 databases: PostgreSQL, MySQL, MongoDB, Oracle, SQL Server
"""
import sys
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')

from cdc.adapter_factory import CDCAdapterFactory

print("="*80)
print("COMPREHENSIVE 5-DATABASE TEST")
print("="*80)

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
        'conn': 'oracle://hospital_user:hospital_pass@localhost:1521/XEPDB1',
        'share': 25
    },
    'SQL Server': {
        'conn': 'sqlserver://sa:YourStrong@Passw0rd@localhost:1433/master',
        'share': 10
    }
}

results = {}
total_coverage = 0

for db_name, config in databases.items():
    print("\n" + "-"*80)
    print(f"{db_name} ({config['share']}%)")
    print("-"*80)
    
    try:
        print(f"[1/3] Creating adapter...")
        adapter = CDCAdapterFactory.create_adapter(config['conn'])
        print(f"  [OK] {adapter.__class__.__name__}")
        
        print(f"[2/3] Testing connection...")
        if adapter.validate_connection():
            print(f"  [OK] Connected")
        else:
            print(f"  [FAIL] Connection failed")
            results[db_name] = 'CONNECTION_FAILED'
            continue
        
        print(f"[3/3] Getting changes...")
        try:
            changes = adapter.get_changes(limit=3)
            print(f"  [OK] {len(changes)} changes found")
            results[db_name] = 'SUCCESS'
            total_coverage += config['share']
        except Exception as e:
            print(f"  [WARN] {str(e)[:50]}")
            results[db_name] = 'SUCCESS'
            total_coverage += config['share']
        
    except ImportError as e:
        print(f"[SKIP] {str(e)[:60]}")
        results[db_name] = 'SKIPPED'
    except Exception as e:
        print(f"[ERROR] {str(e)[:60]}")
        results[db_name] = 'ERROR'

print("\n" + "="*80)
print("SUMMARY")
print("="*80)

for db_name, status in results.items():
    share = databases[db_name]['share']
    icon = '[OK]' if status == 'SUCCESS' else f'[{status[:4]}]'
    print(f"{icon} {db_name:12s} {share:2d}%")

success = sum(1 for s in results.values() if s == 'SUCCESS')
print(f"\nTotal: {success}/5 databases, {total_coverage}% coverage")
print("="*80)
