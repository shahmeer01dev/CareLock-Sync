"""
demo_admin_observability.py — CareLock Sync Demo
FHIR counts, per-hospital quality scores, partition health, CDC lag.
Run:  python demo_admin_observability.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import ADMIN_KEY, call, section, row, divider, dim, bold, green, yellow, red, cyan

TENANT_ID = 1

def _bar(score, width=20):
    score  = float(score or 0)
    filled = round(score / 100 * width)
    bar    = "#" * filled + "." * (width - filled)
    colour = green if score >= 80 else yellow if score >= 60 else red
    return colour(f"[{bar}] {score:.1f}/100")

def run() -> bool:
    section("DEMO 4 — ADMIN OBSERVABILITY")
    all_ok = True

    # 4a — Sync statistics
    print(f"  {cyan('4a. FHIR Resource Statistics')}")
    print(dim("  Calling GET /api/v1/sync/statistics ..."))
    print()
    try:
        _, data, ms = call("GET", "/api/v1/sync/statistics", api_key=ADMIN_KEY)
        tenant = data.get("tenant", {})
        fhir   = data.get("fhir_resources", {})
        state  = data.get("sync_state", {})
        row("Tenant",              f"{tenant.get('name','?')}  ({tenant.get('code','?')})")
        row("Patients in FHIR",    fhir.get("patients",    "?"))
        row("Encounters in FHIR",  fhir.get("encounters",  "?"))
        row("Observations in FHIR",fhir.get("observations","?"))
        row("Medications in FHIR", fhir.get("medications", "?"))
        divider()
        row("Total FHIR records",  fhir.get("total", "?"))
        row("Total syncs run",     state.get("total_syncs", 0))
        row("Last sync at",        state.get("last_sync_time") or dim("—"))
        row("Response time",       f"{ms} ms")
    except Exception as exc:
        print(red(f"  FAILED: {exc}")); all_ok = False
    print()

    # 4b — Data quality dashboard
    print(f"  {cyan('4b. Data Quality Dashboard  (all hospitals)')}")
    print(dim("  Calling GET /api/v1/sync/quality ..."))
    print()
    try:
        _, data, ms = call("GET", "/api/v1/sync/quality", api_key=ADMIN_KEY)
        tenants = data.get("tenants", [])
        if not tenants:
            print(dim("  No hospitals with data yet."))
        else:
            fmt = "  {:<8} {:<28} {:>8}  {:>8}  {}"
            print(dim(fmt.format("Code", "Hospital", "Patients", "HighQ", "Avg Score")))
            divider()
            for t in tenants:
                print(fmt.format(
                    t.get("hospital_code","?"),
                    t.get("hospital_name","?")[:26],
                    t.get("total_patients", 0),
                    t.get("high_quality",   0),
                    _bar(t.get("avg_score", 0)),
                ))
            divider()
            print(f"  {dim('High Quality = completeness score >= 80  (name+DOB+gender+contact+address)')}")
    except Exception as exc:
        print(red(f"  FAILED: {exc}")); all_ok = False
    print()

    # 4c — Tenant deep-dive
    print(f"  {cyan(f'4c. Tenant {TENANT_ID} Deep-Dive  (partition health + CDC lag)')}")
    print(dim(f"  Calling GET /api/v1/connector/tenants/{TENANT_ID}/health ..."))
    print()
    try:
        _, data, ms = call("GET", f"/api/v1/connector/tenants/{TENANT_ID}/health",
                           api_key=ADMIN_KEY)
        q = data.get("data_quality") or {}
        if q:
            print(f"  {bold('Data quality')}")
            divider()
            row("Hospital",       f"{q.get('hospital_name','?')}  [{q.get('hospital_code','?')}]")
            row("DB platform",    q.get("db_platform","?"))
            row("Total patients", q.get("total_patients","?"))
            row("High quality",   q.get("high_quality","?"))
            row("Low quality",    q.get("low_quality", 0), ok=(int(q.get("low_quality",0))==0))
            row("Avg score",      f"{q.get('avg_score','?')}/100")
            print()

        parts = [p for p in data.get("partition_stats",[]) if p.get("live_rows",0) > 0][:4]
        if parts:
            print(f"  {bold('Active partitions')}")
            divider()
            pfmt = "  {:<42} {:>8}  {:>10}  {}"
            print(dim(pfmt.format("Partition", "Rows", "Size", "Vacuum")))
            for p in parts:
                vs = p.get("vacuum_status","OK")
                vc = green("OK") if vs == "OK" else yellow(vs)
                print(pfmt.format(p.get("partition_name","?")[:40],
                                  p.get("live_rows",0),
                                  p.get("total_size","?"),
                                  vc))
            print()

        cdc = data.get("cdc_lag", [])
        if cdc:
            print(f"  {bold('CDC lag')}")
            divider()
            for c in cdc:
                hs = c.get("health_status","OK")
                row("Pending events", c.get("pending_events", 0))
                row("Health",         green("OK") if hs=="OK" else red(hs), ok=(hs=="OK"))
        else:
            print(f"  {bold('CDC lag')}   {green('No backlog  — CDC is current')}")

        row("Response time", f"{ms} ms")
    except Exception as exc:
        print(red(f"  FAILED: {exc}")); all_ok = False
    print()

    result = green("All observability endpoints responding") if all_ok \
             else red("One or more endpoints failed")
    print(f"  {result}")
    print()
    return all_ok

if __name__ == "__main__":
    sys.exit(0 if run() else 1)
