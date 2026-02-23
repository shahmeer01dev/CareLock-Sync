"""
demo_connector_health.py — CareLock Sync Demo
Database connectivity, latency, FHIR counts, tenant registry.
Run:  python demo_connector_health.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import ADMIN_KEY, call, section, row, divider, dim, bold, green, yellow, red, cyan

PLATFORM = {"postgresql":"PostgreSQL","mysql":"MySQL","oracle":"Oracle",
            "sqlserver":"SQL Server","mongodb":"MongoDB"}

def _latency(ms):
    if ms is None: return red("OFFLINE")
    if ms < 100:   return green(f"{ms} ms")
    if ms < 500:   return yellow(f"{ms} ms")
    return red(f"{ms} ms  (slow)")

def run() -> bool:
    section("DEMO 5 — CONNECTOR HEALTH")
    all_ok = True

    # 5a — Database connectivity
    print(f"  {cyan('5a. Database Connectivity')}")
    print(dim("  Calling GET /api/v1/connector/health ..."))
    print()
    try:
        _, data, ms = call("GET", "/api/v1/connector/health", api_key=ADMIN_KEY)
        overall  = data.get("overall","?").upper()
        oc       = green(overall) if overall == "HEALTHY" else red(overall)
        print(f"  {'Overall status':<26} {oc}  {dim(f'(checked in {ms} ms)')}")
        print()

        fmt = "  {:<6} {:<24} {:<14} {}"
        print(dim(fmt.format("", "Database", "Platform", "Latency")))
        divider()
        db_ok = True
        for db in data.get("databases", []):
            conn    = db.get("connected", False)
            db_ok   = db_ok and conn
            icon    = green("UP  ") if conn else red("DOWN")
            name    = db.get("name","?")[:22]
            plat    = PLATFORM.get(db.get("platform",""), db.get("platform",""))[:12]
            lat     = _latency(db.get("latency_ms"))
            print(fmt.format(f"[{icon}]", name, plat, lat))
            if db.get("error"):
                print(f"         {red('Error:')} {dim(db['error'][:70])}")
        divider()
        all_ok = all_ok and db_ok
        print()

        # FHIR counts
        central = data.get("central_db", {})
        if central:
            print(f"  {bold('Central FHIR DB — record counts')}")
            divider()
            total = 0
            for tbl, cnt in central.items():
                label = tbl.replace("fhir_","").replace("_"," ").title()
                row(f"  {label}", cnt)
                total += cnt or 0
            divider()
            row("  Total records", total)
        print()
    except Exception as exc:
        print(red(f"  FAILED: {exc}")); all_ok = False

    # 5b — Connector status
    print(f"  {cyan('5b. Connector Status')}")
    print(dim("  Calling GET /api/v1/connector/status ..."))
    print()
    try:
        _, data, ms = call("GET", "/api/v1/connector/status", api_key=ADMIN_KEY)
        st  = data.get("status","?")
        sc  = green(st.upper()) if st == "operational" else yellow(st.upper())
        cdc = data.get("cdc_enabled", False)
        row("System status",   sc)
        row("Active tenants",  data.get("active_tenants","?"))
        row("CDC enabled",     green("Yes") if cdc else yellow("No"), ok=cdc)
        row("Monitored tables",", ".join(data.get("monitored_tables", [])))
        row("Last CDC event",  data.get("last_cdc_event") or dim("none yet"))
        row("Response time",   f"{ms} ms")
    except Exception as exc:
        print(red(f"  FAILED: {exc}")); all_ok = False
    print()

    # 5c — Tenant registry
    print(f"  {cyan('5c. Registered Hospitals')}")
    print(dim("  Calling GET /api/v1/connector/tenants ..."))
    print()
    try:
        _, data, ms = call("GET", "/api/v1/connector/tenants", api_key=ADMIN_KEY)
        tenants = data if isinstance(data, list) else data.get("tenants", [])
        fmt = "  {:<4} {:<32} {:<8} {:<14} {}"
        print(dim(fmt.format("ID", "Hospital Name", "Code", "Platform", "Status")))
        divider()
        for t in tenants:
            active = t.get("is_active", False)
            print(fmt.format(
                str(t.get("tenant_id","?")),
                t.get("hospital_name","?")[:30],
                t.get("hospital_code","?"),
                PLATFORM.get(t.get("db_platform",""), t.get("db_platform",""))[:12],
                green("Active") if active else red("Inactive"),
            ))
        divider()
        act = sum(1 for t in tenants if t.get("is_active"))
        print(f"  {len(tenants)} hospitals registered  |  {act} active")
    except Exception as exc:
        print(red(f"  FAILED: {exc}")); all_ok = False
    print()

    result = green("Connector infrastructure healthy") if all_ok \
             else red("One or more databases unreachable — see above")
    print(f"  {result}")
    print()
    return all_ok

if __name__ == "__main__":
    sys.exit(0 if run() else 1)
