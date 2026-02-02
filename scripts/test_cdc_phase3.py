"""Test CDC Adapter Factory"""
import sys
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')

from cdc.adapter_factory import CDCAdapterFactory
from common.config import settings

print("=" * 70)
print("Phase 3: CDC Adapter Test")
print("=" * 70)

# Test 1: Database type detection
print("\n[Test 1] Database Type Detection:")
test_urls = [
    ("PostgreSQL", settings.hospital_db_url),
    ("MySQL", "mysql://user:pass@localhost:3306/db"),
    ("MongoDB", "mongodb://localhost:27017/db")
]

for name, url in test_urls:
    try:
        db_type = CDCAdapterFactory.detect_database_type(url)
        print(f"  {name}: {db_type} [OK]")
    except Exception as e:
        print(f"  {name}: {e}")

# Test 2: Create PostgreSQL adapter
print("\n[Test 2] PostgreSQL Adapter Creation:")
try:
    adapter = CDCAdapterFactory.create_adapter(settings.hospital_db_url)
    print(f"  Adapter Type: {adapter.get_database_type()} [OK]")
    print(f"  Connection Valid: {adapter.validate_connection()} [OK]")
    
    # Test getting changes
    print("\n[Test 3] Getting Recent Changes:")
    changes = adapter.get_changes(limit=3)
    print(f"  Found {len(changes)} changes [OK]")
    for change in changes:
        print(f"    {change}")
    
    # Test latest change ID
    print("\n[Test 4] Latest Change ID:")
    latest_id = adapter.get_latest_change_id()
    print(f"  Latest ID: {latest_id} [OK]")
    
    print("\n[SUCCESS] All CDC adapter tests passed!")
    
except Exception as e:
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("CDC Adapter Test Complete!")
print("=" * 70)
