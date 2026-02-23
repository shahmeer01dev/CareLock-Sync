"""
demo_full_sync.py — CareLock Sync Demo
Triggers a full ETL sync for tenant 1 and prints clean metrics.
Run:  python demo_full_sync.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import ADMIN_KEY, call, section, row, divider, dim, bold, green, yellow, red

TENANT_ID  = 1
SYNC_LIMIT = 100

def run() -> bool:
    section("DEMO 1 — FULL SYNC")
    print(f"  {'Target':<26} City General Hospital  (tenant_id={TENANT_ID})")
    print(f"  {'Records per resource':<26} {SYNC_LIMIT}")
    print(f"  {'Auth':<26} ADMIN key")
    divider()
    print()
    print(dim("  Calling POST /api/v1/sync/full ..."))
    print()

    try:
        _, data, ms = call("POST", "/api/v1/sync/full", api_key=ADMIN_KEY,
                           body={"tenant_id": TENANT_ID, "limit": SYNC_LIMIT})
    except Exception as exc:
        print(red(f"  FAILED: {exc}")); return False

    stats = data.get("stats", {})
    status_str = data.get("status", "unknown").upper()
    colour = green if status_str == "COMPLETED" else yellow

    print(f"  {'Status':<26} {colour(status_str)}")
    print(f"  {'Sync ID':<26} {data.get('sync_id', '?')}")
    print(f"  {'Triggered by':<26} {data.get('triggered_by', '?')}")
    print(f"  {'Response time':<26} {ms} ms")
    print()

    hdr = "  {:<16} {:>10}  {:>8}  {:>8}  {:>10}"
    print(dim(hdr.format("Resource", "Extracted", "Loaded", "Errors", "Status")))
    divider()

    total_loaded = 0
    total_errors = 0
    all_ok = True

    for resource in ("patients", "encounters", "observations", "medications"):
        s         = stats.get(resource, {})
        extracted = s.get("extracted", 0)
        loaded    = s.get("loaded",    0)
        errors    = s.get("errors",    0)
        ok        = errors == 0 and loaded == extracted
        all_ok    = all_ok and ok
        total_loaded += loaded
        total_errors += errors
        st = green("OK") if ok else red(f"{errors} error(s)")
        print(hdr.format(resource.capitalize(), extracted, loaded, errors, st))

    divider()
    tc = green("CLEAN") if total_errors == 0 else red("ERRORS")
    print(hdr.format("TOTAL", SYNC_LIMIT * 4, total_loaded, total_errors, tc))
    print()

    if ms > 0:
        rpm = round(total_loaded / (ms / 1000) * 60)
        perf_c = green if rpm >= 10_000 else yellow
        print(f"  {'Performance':<26} {total_loaded} records in {ms} ms  =  {perf_c(f'{rpm:,} records/min')}")
        if rpm >= 10_000:
            print(f"  {green('  Exceeds 10,000 records/min target')}")
    print()
    result = green("Full sync completed successfully") if all_ok else red("Sync completed with errors")
    print(f"  {result}")
    print()
    return all_ok

if __name__ == "__main__":
    sys.exit(0 if run() else 1)
