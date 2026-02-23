"""
demo_incremental_sync.py — CareLock Sync Demo
Inserts a live patient into the hospital DB, then runs incremental CDC sync.
Run:  python demo_incremental_sync.py
"""
import sys, os, time, subprocess, datetime
sys.path.insert(0, os.path.dirname(__file__))
from config import ADMIN_KEY, call, section, row, divider, dim, bold, green, yellow, red

TENANT_ID    = 1
LAST_SYNC_ID = 56
DEMO_MRN     = f"DEMO-{datetime.datetime.now().strftime('%H%M%S')}"

def _psql(container, user, db, sql):
    r = subprocess.run(["docker","exec",container,"psql","-U",user,"-d",db,"-t","-A","-c",sql],
                       capture_output=True, text=True, timeout=10)
    return r.stdout.strip()

def insert_patient():
    sql = (f"INSERT INTO patients (medical_record_number,first_name,last_name,"
           f"date_of_birth,gender,phone_number,email,city) VALUES "
           f"('{DEMO_MRN}','Layla','Hassan','1992-07-14','female',"
           f"'0300-5551234','layla@demo.pk','Karachi') "
           f"ON CONFLICT (medical_record_number) DO NOTHING;")
    try: _psql("carelock_postgres","hospital_user","hospital_db", sql); return True
    except Exception: return False

def get_latest_cdc_id():
    try:
        raw   = _psql("carelock_postgres","hospital_user","hospital_db",
                      "SELECT MAX(change_id) FROM data_change_log;")
        lines = [l.strip() for l in raw.splitlines() if l.strip().isdigit()]
        return int(lines[0]) if lines else None
    except Exception: return None

def check_fhir(mrn):
    try:
        raw   = _psql("carelock_central_fhir","shared_user","carelock_shared",
                      f"SELECT family_name||', '||given_name[1] FROM fhir_patient "
                      f"WHERE identifier_value='{mrn}';")
        lines = [l.strip() for l in raw.splitlines() if l.strip()]
        return lines[0] if lines else None
    except Exception: return None

def run() -> bool:
    section("DEMO 2 — INCREMENTAL SYNC  (CDC-DRIVEN)")

    print(f"  {bold('Step 1')}  Insert a live patient into the hospital database")
    print()
    print(f"  {'MRN':<26} {DEMO_MRN}")
    print(f"  {'Name':<26} Layla Hassan")
    print(f"  {'DOB':<26} 1992-07-14  |  City: Karachi")
    print()
    ok = insert_patient()
    if ok: print(f"  {green('Patient inserted into hospital DB')}")
    else:  print(f"  {yellow('Could not insert (Docker not reachable) — using existing CDC events')}")
    print()

    print(f"  {bold('Step 2')}  CDC trigger auto-captures the change")
    print()
    latest_id = get_latest_cdc_id()
    if latest_id:
        print(f"  {'Latest CDC change_id':<26} {green(str(latest_id))}")
        print(f"  {'Previous watermark':<26} {LAST_SYNC_ID}")
        print(f"  {'New events pending':<26} {yellow(str(latest_id - LAST_SYNC_ID))}")
    else:
        print(f"  {dim('(CDC log not directly readable — proceeding)')}")
        latest_id = LAST_SYNC_ID + 1
    print()

    print(f"  {bold('Step 3')}  Run incremental sync (watermark={LAST_SYNC_ID})")
    print()
    print(dim("  Calling POST /api/v1/sync/incremental ..."))
    print()

    try:
        _, data, ms = call("POST", "/api/v1/sync/incremental", api_key=ADMIN_KEY,
                           body={"tenant_id": TENANT_ID, "last_sync_id": LAST_SYNC_ID})
    except Exception as exc:
        print(red(f"  FAILED: {exc}")); return False

    stats = data.get("stats", {})
    st    = data.get("status","?").upper()
    sc    = green if st == "COMPLETED" else yellow

    print(f"  {'Status':<26} {sc(st)}")
    print(f"  {'Sync ID':<26} {data.get('sync_id','?')}")
    print(f"  {'Response time':<26} {ms} ms")
    print()

    tc  = stats.get("total_changes",  0)
    syn = stats.get("synced",         0)
    err = stats.get("errors",         0)
    lid = stats.get("last_change_id","?")

    divider()
    row("Total CDC changes found",  tc)
    row("Successfully synced",      syn,  ok=(syn == tc))
    row("Errors",                   err,  ok=(err == 0))
    row("New CDC watermark",        lid)
    divider()
    print()

    print(f"  {bold('Step 4')}  Verify patient appeared in FHIR database")
    print()
    time.sleep(0.3)
    fhir_name = check_fhir(DEMO_MRN)
    if fhir_name:
        print(f"  {green('Patient confirmed in FHIR DB')}  ->  {fhir_name}")
    else:
        print(f"  {yellow('Patient not yet in FHIR DB')} {dim('(may need full sync if MRN outside CDC window)')}")

    print()
    all_ok = err == 0 and syn > 0
    result = green("Incremental sync completed — only delta records processed") if all_ok \
             else yellow("Sync ran — check output above")
    print(f"  {result}")
    print()
    return all_ok

if __name__ == "__main__":
    sys.exit(0 if run() else 1)
