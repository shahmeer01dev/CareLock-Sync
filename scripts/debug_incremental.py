"""
Debug incremental CDC sync end-to-end  (correct credentials)
"""
import sys, os, traceback
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\etl')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\connector')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\schema-mapper')

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

HOSPITAL_URL = "postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db"
SHARED_URL   = "postgresql://shared_user:shared_pass@localhost:5433/carelock_shared"

hospital_eng = create_engine(HOSPITAL_URL)
shared_eng   = create_engine(SHARED_URL)

# ── 1. What is in data_change_log? ───────────────────────────────────────────
print("=" * 70)
print("STEP 1 – data_change_log contents")
print("=" * 70)
with hospital_eng.connect() as conn:
    rows = conn.execute(text(
        "SELECT change_id, table_name, operation, record_id, changed_at "
        "FROM data_change_log ORDER BY change_id DESC LIMIT 15"
    )).fetchall()
    print(f"  Total rows: {len(rows)}")
    for r in rows:
        print(f"    id={r[0]:>4}  table={r[1]:<15} op={r[2]:<8} rec_id={r[3]}  at={r[4]}")

# ── 2. Which tables have triggers? ───────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 2 – Installed CDC triggers")
print("=" * 70)
with hospital_eng.connect() as conn:
    trigs = conn.execute(text(
        "SELECT trigger_name, event_object_table, event_manipulation "
        "FROM information_schema.triggers WHERE trigger_schema = 'public'"
    )).fetchall()
    if trigs:
        for t in trigs:
            print(f"    {t[0]:<40} table={t[1]:<20} event={t[2]}")
    else:
        print("    !! NO triggers found – CDC is not set up")

# ── 3. Shared DB – fhir_patient count ────────────────────────────────────────
print("\n" + "=" * 70)
print("STEP 3 – fhir_patient in shared DB")
print("=" * 70)
with shared_eng.connect() as conn:
    cnt = conn.execute(text("SELECT COUNT(*) FROM fhir_patient")).scalar()
    print(f"  fhir_patient rows: {cnt}")

# ── 4. Manually INSERT one patient change into the log, then sync it ─────────
print("\n" + "=" * 70)
print("STEP 4 – Insert a test patient UPDATE, then run incremental sync")
print("=" * 70)

# pick an arbitrary patient
with hospital_eng.connect() as conn:
    pid = conn.execute(text("SELECT patient_id FROM patients LIMIT 1")).scalar()
    print(f"  Picked patient_id = {pid}")

    # manually update that patient so the trigger fires a new change_log row
    conn.execute(text(
        "UPDATE patients SET last_name = last_name WHERE patient_id = :pid"
    ), {"pid": pid})
    conn.commit()

    # check what the trigger wrote
    new_row = conn.execute(text(
        "SELECT change_id, table_name, operation, record_id "
        "FROM data_change_log ORDER BY change_id DESC LIMIT 1"
    )).fetchone()
    print(f"  New change_log row: {new_row}")
    last_change_id = new_row[0] if new_row else None

# ── 5. Now call sync_incremental with last_sync_id = (last_change_id - 1) ────
print("\n" + "=" * 70)
print("STEP 5 – IncrementalSync.sync_incremental()")
print("=" * 70)
try:
    from incremental_sync import IncrementalSync
    sync = IncrementalSync(tenant_id=1)
    # override the cdc_monitor connection string so it uses the right creds
    sync.cdc_monitor.database_url = HOSPITAL_URL
    sync.cdc_monitor.engine = hospital_eng

    start_id = (last_change_id - 1) if last_change_id else 0
    print(f"  Calling sync_incremental(last_sync_id={start_id})")
    stats = sync.sync_incremental(last_sync_id=start_id)
    print("\n  Returned stats:", stats)
except Exception:
    print("  !! EXCEPTION:")
    traceback.print_exc()

print("\n" + "=" * 70)
print("DEBUG COMPLETE")
print("=" * 70)
