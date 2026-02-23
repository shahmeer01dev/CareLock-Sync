"""
Diagnose incremental CDC sync
"""
import sys, os, traceback
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\etl')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\connector')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\schema-mapper')

from dotenv import load_dotenv
load_dotenv(r'C:\Projects\CareLock-Sync\backend\.env')

from common.database import hospital_db_session, shared_db_session
from sqlalchemy import text

print("=" * 60)
print("STEP 1 — What is in data_change_log?")
print("=" * 60)
with hospital_db_session() as db:
    rows = db.execute(text(
        "SELECT change_id, table_name, operation, record_id, changed_at "
        "FROM data_change_log ORDER BY change_id DESC LIMIT 10"
    )).fetchall()
    if rows:
        for r in rows:
            print(f"  id={r[0]}  table={r[1]}  op={r[2]}  rec_id={r[3]}  at={r[4]}")
    else:
        print("  TABLE IS EMPTY — no changes have been logged yet")

print()
print("=" * 60)
print("STEP 2 — What is already in fhir_patient (shared DB)?")
print("=" * 60)
with shared_db_session() as db:
    rows = db.execute(text(
        "SELECT id, tenant_id, source_patient_id, family_name "
        "FROM fhir_patient LIMIT 5"
    )).fetchall()
    if rows:
        for r in rows:
            print(f"  id={r[0]}  tenant={r[1]}  src_pat={r[2]}  family={r[3]}")
    else:
        print("  TABLE IS EMPTY — nothing synced yet")

print()
print("=" * 60)
print("STEP 3 — Run IncrementalSync (last_sync_id=None)")
print("=" * 60)
try:
    from incremental_sync import IncrementalSync
    sync = IncrementalSync(tenant_id=1)
    stats = sync.sync_incremental(last_sync_id=None)
    print("\nSTATS:", stats)
except Exception as e:
    print(f"\n  EXCEPTION: {e}")
    traceback.print_exc()

print()
print("=" * 60)
print("STEP 4 — Insert a brand-new patient, then sync again")
print("=" * 60)
try:
    with hospital_db_session() as db:
        db.execute(text("""
            INSERT INTO patients (
                medical_record_number, first_name, last_name,
                date_of_birth, gender
            ) VALUES ('TEST-CDC-001', 'CDC', 'TestPatient', '1990-06-15', 'Male')
        """))
        db.commit()
        print("  Inserted TEST patient TEST-CDC-001")

        # check what change_id was written
        row = db.execute(text(
            "SELECT change_id, table_name, operation, record_id "
            "FROM data_change_log ORDER BY change_id DESC LIMIT 1"
        )).fetchone()
        if row:
            print(f"  New change logged: id={row[0]}  table={row[1]}  op={row[2]}  rec_id={row[3]}")
            new_change_id = row[0]
        else:
            print("  WARNING: no new change_id appeared — trigger may be broken")
            new_change_id = None
except Exception as e:
    print(f"  EXCEPTION during insert: {e}")
    traceback.print_exc()
    new_change_id = None

print()
print("=" * 60)
print("STEP 5 — Incremental sync from change_id BEFORE new patient")
print("=" * 60)
try:
    sync2 = IncrementalSync(tenant_id=1)
    # use new_change_id - 1 so the new row is included
    since = (new_change_id - 1) if new_change_id else None
    print(f"  Syncing since change_id > {since}")
    stats2 = sync2.sync_incremental(last_sync_id=since)
    print("\nSTATS:", stats2)
except Exception as e:
    print(f"  EXCEPTION: {e}")
    traceback.print_exc()

print()
print("=" * 60)
print("STEP 6 — Confirm new patient is now in fhir_patient")
print("=" * 60)
with shared_db_session() as db:
    row = db.execute(text(
        "SELECT id, source_patient_id, family_name "
        "FROM fhir_patient WHERE family_name = 'TestPatient'"
    )).fetchone()
    if row:
        print(f"  FOUND: id={row[0]}  src={row[1]}  family={row[2]}")
    else:
        print("  NOT FOUND — sync did not write this patient")

# Clean-up test patient
print()
print("CLEANUP — removing test patient")
with hospital_db_session() as db:
    db.execute(text("DELETE FROM patients WHERE medical_record_number = 'TEST-CDC-001'"))
    db.commit()
