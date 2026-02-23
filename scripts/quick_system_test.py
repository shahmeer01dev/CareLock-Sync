"""
Quick System Test - Non-Interactive
Tests all major components without requiring user input
"""
import sys
import os

sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
os.environ['PATH'] = r'C:\oracle\instantclient_23_0;' + os.environ.get('PATH', '')

print("=" * 80)
print("CARELOCK SYNC - AUTOMATED SYSTEM TEST")
print("=" * 80)

# Test 1: All 5 Databases
print("\n[TEST 1] Testing all 5 databases...")
try:
    exec(open(r'C:\Projects\CareLock-Sync\scripts\test_all_5_databases_final.py').read())
    print("  [OK] All 5 databases tested")
except Exception as e:
    print(f"  [ERROR] {e}")

# Test 2: Central Database Connection
print("\n[TEST 2] Testing central FHIR database...")
try:
    import psycopg2
    conn = psycopg2.connect(
        host='localhost',
        port=5433,
        database='carelock_shared',
        user='shared_user',
        password='shared_pass'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM fhir_patient")
    count = cursor.fetchone()[0]
    print(f"  [OK] Central database connected - {count} patients")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"  [ERROR] {e}")

# Test 3: ETL Pipeline
print("\n[TEST 3] Testing ETL pipeline...")
try:
    from etl.pipeline import ETLPipeline
    pipeline = ETLPipeline(tenant_id=1)
    result = pipeline.sync_all(limit=5)
    print(f"  [OK] ETL pipeline working - synced {result}")
except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()

# Test 4: Incremental Sync
print("\n[TEST 4] Testing incremental sync...")
try:
    from etl.incremental_sync import IncrementalSync
    sync = IncrementalSync(tenant_id=1)
    stats = sync.sync_incremental(last_sync_id=0)
    print(f"  [OK] Incremental sync working")
    print(f"       Total changes: {stats.get('total_changes', 0)}")
    print(f"       Synced: {stats.get('synced', 0)}")
    print(f"       Errors: {stats.get('errors', 0)}")
except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()

# Test 5: Check Central Database Data
print("\n[TEST 5] Checking synchronized data in central database...")
try:
    import psycopg2
    conn = psycopg2.connect(
        host='localhost',
        port=5433,
        database='carelock_shared',
        user='shared_user',
        password='shared_pass'
    )
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM fhir_patient")
    patients = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fhir_encounter")
    encounters = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM fhir_observation")
    observations = cursor.fetchone()[0]
    
    print(f"  [OK] Central database statistics:")
    print(f"       Patients: {patients}")
    print(f"       Encounters: {encounters}")
    print(f"       Observations: {observations}")
    
    cursor.close()
    conn.close()
except Exception as e:
    print(f"  [ERROR] {e}")

print("\n" + "=" * 80)
print("AUTOMATED TEST COMPLETE")
print("=" * 80)
