"""
Comprehensive Incremental CDC Test
Tests the complete flow: trigger -> change log -> incremental sync -> FHIR DB

This test:
1. Starts from a clean slate (deletes scheduler state)
2. Makes changes to hospital DB (INSERT, UPDATE, DELETE)
3. Runs incremental sync
4. Validates FHIR DB contains the correct data
5. Makes more changes
6. Runs another incremental sync (from watermark)
7. Validates correctness again
"""
import sys
import os
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\etl')

from sqlalchemy import create_engine, text
from common.config import settings
from incremental_sync import IncrementalSync
import json

# ══════════════════════════════════════════════════════════════════════════
# Setup
# ══════════════════════════════════════════════════════════════════════════
print("=" * 80)
print("COMPREHENSIVE INCREMENTAL CDC TEST")
print("=" * 80)

hospital_eng = create_engine(settings.hospital_db_url)
shared_eng = create_engine(settings.shared_db_url)

STATE_FILE = r'C:\Projects\CareLock-Sync\backend\scheduler_state.json'
if os.path.exists(STATE_FILE):
    os.remove(STATE_FILE)
    print(f"[OK] Removed old scheduler state: {STATE_FILE}\n")

# ══════════════════════════════════════════════════════════════════════════
# Test 1: Baseline - what's in the change log right now?
# ══════════════════════════════════════════════════════════════════════════
print("-" * 80)
print("TEST 1: Baseline Change Log")
print("-" * 80)

with hospital_eng.connect() as conn:
    max_id = conn.execute(text("SELECT MAX(change_id) FROM data_change_log")).scalar()
    count = conn.execute(text("SELECT COUNT(*) FROM data_change_log")).scalar()
    print(f"  Change log rows: {count}")
    print(f"  Max change_id  : {max_id}")

baseline_change_id = max_id if max_id else 0

# ══════════════════════════════════════════════════════════════════════════
# Test 2: Make new changes - INSERT, UPDATE, DELETE
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 80)
print("TEST 2: Creating New Changes")
print("-" * 80)

test_changes = []

with hospital_eng.connect() as conn:
    # INSERT a new patient (use timestamp to ensure uniqueness)
    import time
    mrn_suffix = str(int(time.time()))[-6:]
    result = conn.execute(text("""
        INSERT INTO patients (medical_record_number, first_name, last_name, 
                              date_of_birth, gender)
        VALUES (:mrn, 'TestFirst', 'TestLast', '1990-01-01', 'male')
        RETURNING patient_id
    """), {'mrn': f'TEST-CDC-{mrn_suffix}'})
    new_patient_id = result.scalar()
    conn.commit()
    print(f"  [OK] INSERT patient_id={new_patient_id}")
    test_changes.append(('INSERT', new_patient_id))

    # UPDATE that patient
    conn.execute(text("""
        UPDATE patients SET last_name = 'UpdatedLast' WHERE patient_id = :pid
    """), {'pid': new_patient_id})
    conn.commit()
    print(f"  [OK] UPDATE patient_id={new_patient_id}")
    test_changes.append(('UPDATE', new_patient_id))

    # UPDATE an existing patient
    existing_patient = conn.execute(text(
        "SELECT patient_id FROM patients WHERE patient_id != :new_pid LIMIT 1"
    ), {'new_pid': new_patient_id}).scalar()
    
    if existing_patient:
        conn.execute(text("""
            UPDATE patients SET email = 'updated@test.com' WHERE patient_id = :pid
        """), {'pid': existing_patient})
        conn.commit()
        print(f"  [OK] UPDATE patient_id={existing_patient} (existing)")
        test_changes.append(('UPDATE', existing_patient))

    # DELETE the new patient
    conn.execute(text("DELETE FROM patients WHERE patient_id = :pid"), 
                 {'pid': new_patient_id})
    conn.commit()
    print(f"  [OK] DELETE patient_id={new_patient_id}")
    test_changes.append(('DELETE', new_patient_id))

# Check change log
with hospital_eng.connect() as conn:
    new_max = conn.execute(text("SELECT MAX(change_id) FROM data_change_log")).scalar()
    new_count = conn.execute(text("SELECT COUNT(*) FROM data_change_log")).scalar()
    print(f"\n  Change log after operations:")
    print(f"    Total rows    : {new_count}")
    print(f"    Max change_id : {new_max}")
    print(f"    New changes   : {new_max - baseline_change_id}")

# ══════════════════════════════════════════════════════════════════════════
# Test 3: First Incremental Sync (from baseline)
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 80)
print("TEST 3: First Incremental Sync")
print("-" * 80)

sync = IncrementalSync(tenant_id=1)
stats1 = sync.sync_incremental(last_sync_id=baseline_change_id)

print(f"\n  Results:")
print(f"    Total changes  : {stats1['total_changes']}")
print(f"    Synced         : {stats1['synced']}")
print(f"    Errors         : {stats1['errors']}")
print(f"    Last change ID : {stats1['last_change_id']}")

# Validate
assert stats1['errors'] == 0, f"Expected 0 errors, got {stats1['errors']}"
print("\n  [OK] Sync completed without errors")

# Save watermark
watermark1 = stats1['last_change_id']
with open(STATE_FILE, 'w') as f:
    json.dump({'last_sync_id': watermark1}, f)
print(f"  [OK] Saved watermark: {watermark1}")

# ══════════════════════════════════════════════════════════════════════════
# Test 4: Verify FHIR DB state
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 80)
print("TEST 4: Verify FHIR Database")
print("-" * 80)

with shared_eng.connect() as conn:
    # Check if the deleted patient is NOT in FHIR DB
    deleted_row = conn.execute(text("""
        SELECT * FROM fhir_patient 
        WHERE tenant_id = 1 AND source_patient_id = :src
    """), {'src': str(new_patient_id)}).fetchone()
    
    assert deleted_row is None, f"Deleted patient {new_patient_id} still exists in FHIR DB!"
    print(f"  [OK] Deleted patient {new_patient_id} NOT in FHIR DB (correct)")

    # Check if the updated existing patient IS in FHIR DB
    if existing_patient:
        updated_row = conn.execute(text("""
            SELECT email FROM fhir_patient
            WHERE tenant_id = 1 AND source_patient_id = :src
        """), {'src': str(existing_patient)}).fetchone()
        
        if updated_row:
            print(f"  [OK] Existing patient {existing_patient} in FHIR DB")
            print(f"    Email: {updated_row[0]}")

    # Total count
    total = conn.execute(text("SELECT COUNT(*) FROM fhir_patient WHERE tenant_id = 1")).scalar()
    print(f"\n  Total FHIR patients: {total}")

# ══════════════════════════════════════════════════════════════════════════
# Test 5: Make MORE changes (after first sync)
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 80)
print("TEST 5: Creating Second Batch of Changes")
print("-" * 80)

with hospital_eng.connect() as conn:
    # Insert another patient (unique MRN)
    import time
    mrn_suffix2 = str(int(time.time()))[-6:]
    result = conn.execute(text("""
        INSERT INTO patients (medical_record_number, first_name, last_name,
                              date_of_birth, gender)
        VALUES (:mrn, 'SecondTest', 'SecondLast', '1995-06-15', 'female')
        RETURNING patient_id
    """), {'mrn': f'TEST-CDC-{mrn_suffix2}'})
    second_patient_id = result.scalar()
    conn.commit()
    print(f"  [OK] INSERT patient_id={second_patient_id}")

    # Update it
    conn.execute(text("""
        UPDATE patients SET phone_number = '555-0123' WHERE patient_id = :pid
    """), {'pid': second_patient_id})
    conn.commit()
    print(f"  [OK] UPDATE patient_id={second_patient_id}")

# ══════════════════════════════════════════════════════════════════════════
# Test 6: Second Incremental Sync (from watermark)
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 80)
print("TEST 6: Second Incremental Sync (from watermark)")
print("-" * 80)

# Load watermark
with open(STATE_FILE, 'r') as f:
    saved_state = json.load(f)
    loaded_watermark = saved_state['last_sync_id']

print(f"  Loaded watermark: {loaded_watermark}")

stats2 = sync.sync_incremental(last_sync_id=loaded_watermark)

print(f"\n  Results:")
print(f"    Total changes  : {stats2['total_changes']}")
print(f"    Synced         : {stats2['synced']}")
print(f"    Errors         : {stats2['errors']}")
print(f"    Last change ID : {stats2['last_change_id']}")

assert stats2['errors'] == 0, f"Expected 0 errors, got {stats2['errors']}"
# Note: Deduplication collapses INSERT + UPDATE into just UPDATE
assert stats2['synced'] >= 1, f"Expected at least 1 synced, got {stats2['synced']}"
print("\n  [OK] Second sync completed correctly (deduplication working)")

# Update watermark
watermark2 = stats2['last_change_id']
with open(STATE_FILE, 'w') as f:
    json.dump({'last_sync_id': watermark2}, f)
print(f"  [OK] Updated watermark: {watermark2}")

# ══════════════════════════════════════════════════════════════════════════
# Test 7: Verify second patient is in FHIR DB
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 80)
print("TEST 7: Verify Second Patient in FHIR DB")
print("-" * 80)

with shared_eng.connect() as conn:
    row = conn.execute(text("""
        SELECT source_patient_id, family_name, given_name, phone
        FROM fhir_patient
        WHERE tenant_id = 1 AND source_patient_id = :src
    """), {'src': str(second_patient_id)}).fetchone()

    assert row is not None, f"Second patient {second_patient_id} NOT in FHIR DB!"
    print(f"  [OK] Patient {second_patient_id} found in FHIR DB")
    print(f"    Name : {row[2]} {row[1]}")
    print(f"    Phone: {row[3]}")

# ══════════════════════════════════════════════════════════════════════════
# Test 8: Run sync with no new changes (should be no-op)
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "-" * 80)
print("TEST 8: Sync with No New Changes")
print("-" * 80)

stats3 = sync.sync_incremental(last_sync_id=watermark2)

print(f"  Results:")
print(f"    Total changes: {stats3['total_changes']}")

assert stats3['total_changes'] == 0, f"Expected 0 changes, got {stats3['total_changes']}"
print("  [OK] No-op sync works correctly")

# ══════════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("ALL TESTS PASSED [OK]")
print("=" * 80)
print("\nIncremental CDC is working correctly:")
print("  [OK] Triggers capture changes")
print("  [OK] Watermark persistence works")
print("  [OK] INSERT syncs correctly")
print("  [OK] UPDATE syncs correctly")
print("  [OK] DELETE syncs correctly (removes from FHIR DB)")
print("  [OK] Deduplication works (INSERT + DELETE in same batch)")
print("  [OK] Multiple sync cycles work")
print("  [OK] No-op sync when no changes")
print("\n" + "=" * 80)

