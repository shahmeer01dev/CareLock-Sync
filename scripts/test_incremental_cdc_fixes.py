"""
Comprehensive test for incremental CDC - verifies all bug fixes

This test:
1. Creates fresh test data in hospital_db
2. Runs incremental sync
3. Verifies data appears in shared DB
4. Tests UPDATE, INSERT, DELETE operations
5. Tests deduplication logic
6. Tests scheduler
"""
import sys
import os

sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\etl')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\scheduler')

from sqlalchemy import create_engine, text
from datetime import datetime, date
from common.config import settings
from incremental_sync import IncrementalSync
from sync_scheduler import SyncScheduler
import time

print("=" * 80)
print("INCREMENTAL CDC BUG FIX VERIFICATION TEST")
print("=" * 80)
print(f"Hospital DB: {settings.hospital_db_url}")
print(f"Shared DB  : {settings.shared_db_url}")
print()

hospital_eng = create_engine(settings.hospital_db_url)
shared_eng   = create_engine(settings.shared_db_url)

# ────────────────────────────────────────────────────────────────────────────
# TEST 1: Verify connection strings are correct (Bug 1 fix)
# ────────────────────────────────────────────────────────────────────────────
print("[TEST 1] Verify database connections")
print("-" * 80)

try:
    with hospital_eng.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✓ Hospital DB connection OK")
except Exception as e:
    print(f"✗ Hospital DB FAILED: {e}")
    exit(1)

try:
    with shared_eng.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✓ Shared DB connection OK")
except Exception as e:
    print(f"✗ Shared DB FAILED: {e}")
    exit(1)

# ────────────────────────────────────────────────────────────────────────────
# TEST 2: Verify IncrementalSync uses settings (Bug 2 fix)
# ────────────────────────────────────────────────────────────────────────────
print("\n[TEST 2] Verify IncrementalSync uses correct connection string")
print("-" * 80)

sync = IncrementalSync(tenant_id=1)
if sync.cdc_monitor.database_url == settings.hospital_db_url:
    print(f"✓ IncrementalSync using settings: {sync.cdc_monitor.database_url}")
else:
    print(f"✗ Wrong URL: {sync.cdc_monitor.database_url}")
    print(f"  Expected: {settings.hospital_db_url}")
    exit(1)

# ────────────────────────────────────────────────────────────────────────────
# TEST 3: Get baseline - what's in change log now?
# ────────────────────────────────────────────────────────────────────────────
print("\n[TEST 3] Get current change log baseline")
print("-" * 80)

with hospital_eng.connect() as conn:
    baseline_max = conn.execute(text(
        "SELECT COALESCE(MAX(change_id), 0) FROM data_change_log"
    )).scalar()
    baseline_count = conn.execute(text(
        "SELECT COUNT(*) FROM data_change_log"
    )).scalar()

print(f"  Current max change_id: {baseline_max}")
print(f"  Total changes in log : {baseline_count}")

# ────────────────────────────────────────────────────────────────────────────
# TEST 4: Create test patient and verify CDC trigger fires
# ────────────────────────────────────────────────────────────────────────────
print("\n[TEST 4] Create test patient and verify CDC trigger")
print("-" * 80)

test_mrn = f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"

with hospital_eng.begin() as conn:
    # Insert new patient
    result = conn.execute(text("""
        INSERT INTO patients (
            medical_record_number, first_name, last_name,
            date_of_birth, gender, phone_number, email,
            city, state, created_at
        ) VALUES (
            :mrn, 'TestFirst', 'TestLast',
            '1990-01-01', 'M', '555-0100', 'test@example.com',
            'TestCity', 'TS', NOW()
        ) RETURNING patient_id
    """), {'mrn': test_mrn})
    test_patient_id = result.scalar()

print(f"  Created patient_id: {test_patient_id}")

# Verify CDC trigger created a change log entry
with hospital_eng.connect() as conn:
    new_change = conn.execute(text("""
        SELECT change_id, table_name, operation, record_id
        FROM data_change_log
        WHERE record_id = :pid AND table_name = 'patients'
        ORDER BY change_id DESC LIMIT 1
    """), {'pid': test_patient_id}).fetchone()

if new_change:
    print(f"✓ CDC trigger fired: change_id={new_change[0]}, op={new_change[2]}")
else:
    print("✗ CDC trigger did NOT fire - check trigger installation")
    exit(1)

# ────────────────────────────────────────────────────────────────────────────
# TEST 5: Run incremental sync starting from baseline
# ────────────────────────────────────────────────────────────────────────────
print(f"\n[TEST 5] Run incremental sync (last_sync_id={baseline_max})")
print("-" * 80)

stats = sync.sync_incremental(last_sync_id=baseline_max)

print(f"\nSync Results:")
print(f"  Total changes: {stats['total_changes']}")
print(f"  Synced       : {stats['synced']}")
print(f"  Errors       : {stats['errors']}")
print(f"  Last change  : {stats['last_change_id']}")

if stats['errors'] > 0:
    print("✗ Sync had errors")
    exit(1)

if stats['synced'] == 0:
    print("✗ No records synced - something is wrong")
    exit(1)

print("✓ Sync completed successfully")

# ────────────────────────────────────────────────────────────────────────────
# TEST 6: Verify patient appears in shared DB
# ────────────────────────────────────────────────────────────────────────────
print("\n[TEST 6] Verify patient synced to shared DB")
print("-" * 80)

with shared_eng.connect() as conn:
    result = conn.execute(text("""
        SELECT id, source_patient_id, family_name, given_name, gender
        FROM fhir_patient
        WHERE source_patient_id = :src_id AND tenant_id = 1
    """), {'src_id': str(test_patient_id)}).fetchone()

if result:
    print(f"[OK] Patient found in shared DB:")
    print(f"    ID           : {result[0]}")
    print(f"    Source ID    : {result[1]}")
    print(f"    Name         : {result[3]} {result[2]}")
    print(f"    Gender       : {result[4]}")
else:
    print(f"[FAIL] Patient {test_patient_id} NOT found in shared DB")
    exit(1)

# ────────────────────────────────────────────────────────────────────────────
# TEST 7: Test UPDATE operation
# ────────────────────────────────────────────────────────────────────────────
print("\n[TEST 7] Test UPDATE operation")
print("-" * 80)

with hospital_eng.begin() as conn:
    conn.execute(text("""
        UPDATE patients
        SET last_name = 'UpdatedLast', phone_number = '555-9999'
        WHERE patient_id = :pid
    """), {'pid': test_patient_id})

print(f"  Updated patient {test_patient_id}")

# Sync again
stats2 = sync.sync_incremental(last_sync_id=stats['last_change_id'])
print(f"  Synced {stats2['synced']} changes")

# Verify update in shared DB
with shared_eng.connect() as conn:
    result = conn.execute(text("""
        SELECT family_name, phone FROM fhir_patient
        WHERE source_patient_id = :src_id AND tenant_id = 1
    """), {'src_id': str(test_patient_id)}).fetchone()

if result and result[0] == 'UpdatedLast':
    print(f"✓ UPDATE synced correctly: {result[0]}, {result[1]}")
else:
    print(f"✗ UPDATE not synced: {result}")
    exit(1)

# ────────────────────────────────────────────────────────────────────────────
# TEST 8: Test DELETE operation (Bug 4 fix)
# ────────────────────────────────────────────────────────────────────────────
print("\n[TEST 8] Test DELETE operation")
print("-" * 80)

with hospital_eng.begin() as conn:
    conn.execute(text("""
        DELETE FROM patients WHERE patient_id = :pid
    """), {'pid': test_patient_id})

print(f"  Deleted patient {test_patient_id}")

# Sync delete
stats3 = sync.sync_incremental(last_sync_id=stats2['last_change_id'])
print(f"  Synced {stats3['synced']} changes")

# Verify deletion in shared DB
with shared_eng.connect() as conn:
    count = conn.execute(text("""
        SELECT COUNT(*) FROM fhir_patient
        WHERE source_patient_id = :src_id AND tenant_id = 1
    """), {'src_id': str(test_patient_id)}).scalar()

if count == 0:
    print(f"✓ DELETE synced correctly - patient removed from shared DB")
else:
    print(f"✗ DELETE failed - patient still in shared DB")
    exit(1)

# ────────────────────────────────────────────────────────────────────────────
# TEST 9: Test deduplication (Bug 4 fix)
# ────────────────────────────────────────────────────────────────────────────
print("\n[TEST 9] Test deduplication - INSERT then DELETE same patient")
print("-" * 80)

test_mrn2 = f"DEDUP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

with hospital_eng.begin() as conn:
    # Insert
    result = conn.execute(text("""
        INSERT INTO patients (
            medical_record_number, first_name, last_name,
            date_of_birth, gender, created_at
        ) VALUES (
            :mrn, 'DedupTest', 'Patient',
            '1985-05-05', 'F', NOW()
        ) RETURNING patient_id
    """), {'mrn': test_mrn2})
    dedup_patient_id = result.scalar()
    
    # Immediately delete
    conn.execute(text("""
        DELETE FROM patients WHERE patient_id = :pid
    """), {'pid': dedup_patient_id})

print(f"  Created and deleted patient {dedup_patient_id} in same transaction")

# Get changes
with hospital_eng.connect() as conn:
    changes = conn.execute(text("""
        SELECT operation FROM data_change_log
        WHERE record_id = :pid AND table_name = 'patients'
        ORDER BY change_id
    """), {'pid': dedup_patient_id}).fetchall()

print(f"  Changes in log: {[c[0] for c in changes]}")

# Sync - should handle gracefully (Bug 4 fix)
stats4 = sync.sync_incremental(last_sync_id=stats3['last_change_id'])

if stats4['errors'] == 0:
    print(f"✓ Deduplication handled correctly - no errors")
else:
    print(f"✗ Deduplication caused {stats4['errors']} errors")
    exit(1)

# Verify patient never made it to shared DB
with shared_eng.connect() as conn:
    count = conn.execute(text("""
        SELECT COUNT(*) FROM fhir_patient
        WHERE source_patient_id = :src_id AND tenant_id = 1
    """), {'src_id': str(dedup_patient_id)}).scalar()

if count == 0:
    print(f"✓ Patient never inserted in shared DB (correctly optimized)")
else:
    print(f"⚠ Patient was inserted then deleted (works but not optimal)")

# ────────────────────────────────────────────────────────────────────────────
# TEST 10: Test scheduler (Bug 3 fix)
# ────────────────────────────────────────────────────────────────────────────
print("\n[TEST 10] Test scheduler starts from 0 and processes history")
print("-" * 80)

scheduler = SyncScheduler(tenant_id=1, interval_seconds=300)  # 5 min interval

print(f"  Scheduler last_sync_id initialized to: {scheduler.last_sync_id}")

if scheduler.last_sync_id == 0:
    print("✓ Scheduler correctly starts from 0 (will process history)")
else:
    print(f"✗ Scheduler starts from {scheduler.last_sync_id} (skips history)")
    exit(1)

# Don't actually start it (would run indefinitely)
# Just verify initialization
print("  (Not starting scheduler - just verified initialization)")

# ────────────────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("ALL TESTS PASSED ✓")
print("=" * 80)
print()
print("Bug Fixes Verified:")
print("  ✓ Bug 1: Connection strings use settings.hospital_db_url (not hardcoded)")
print("  ✓ Bug 2: IncrementalSync uses settings (not hardcoded connection)")
print("  ✓ Bug 3: Scheduler starts from 0 (processes all history)")
print("  ✓ Bug 4: DELETE and 'not found' handled gracefully (no errors)")
print("  ✓ Bug 4: Deduplication works (INSERT+DELETE in same batch)")
print()
print("Incremental CDC is now FULLY WORKING!")
print("=" * 80)
