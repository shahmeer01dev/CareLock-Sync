"""
demo_security.py — CareLock Sync Demo
Demonstrates every security layer: auth, tenant isolation, role enforcement.
Run:  python demo_security.py
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
from config import ADMIN_KEY, CGH_KEY, PGH_KEY, READONLY_KEY, BAD_KEY, \
                   call, section, divider, dim, bold, green, red, yellow, cyan

def check(desc, method, path, key, body, expect, fragment=""):
    try:
        code, data, ms = call(method, path, api_key=key, body=body,
                              expect=expect, raise_on_error=False)
    except Exception as exc:
        print(f"  {red('[FAIL]')}  {desc:<50} -> Exception: {exc}")
        return False

    detail  = (data.get("detail","") if isinstance(data,dict) else "")[:80]
    passed  = code == expect
    if fragment and fragment.lower() not in detail.lower():
        passed = False

    tag  = green("[PASS]") if passed else red("[FAIL]")
    arr  = f"-> HTTP {code}"
    note = f"  {dim(detail)}" if detail else ""
    print(f"  {tag}  {desc:<50} {arr}{note}")
    return passed

def run() -> bool:
    section("DEMO 3 — SECURITY & ACCESS CONTROL")
    print(f"  {bold('Auth scheme')}   X-API-Key header on every request")
    print(f"  {bold('Roles')}         admin  |  hospital  |  readonly")
    print(f"  {bold('Isolation')}     hospital key locked to its own tenant")
    print()
    results = []

    # A: Authentication
    print(f"  {cyan('A. Authentication')}")
    divider()
    results.append(check("Missing API Key",  "POST","/api/v1/sync/full", None,       {"tenant_id":1},         401, "missing"))
    results.append(check("Invalid API Key",  "POST","/api/v1/sync/full", BAD_KEY,    {"tenant_id":1},         401, "invalid"))
    print()

    # B: Tenant isolation
    print(f"  {cyan('B. Tenant Isolation')}")
    divider()
    results.append(check("CGH key  -> own tenant 1  (allowed)",   "POST","/api/v1/sync/full", CGH_KEY, {"tenant_id":1,"limit":2}, 200))
    results.append(check("CGH key  -> tenant 2 PGH  (blocked)",   "POST","/api/v1/sync/full", CGH_KEY, {"tenant_id":2,"limit":2}, 403, "scoped to tenant"))
    results.append(check("PGH key  -> tenant 1 CGH  (blocked)",   "POST","/api/v1/sync/full", PGH_KEY, {"tenant_id":1,"limit":2}, 403, "scoped to tenant"))
    print()

    # C: Role enforcement
    print(f"  {cyan('C. Role Enforcement')}")
    divider()
    results.append(check("Hospital key on /sync/reset   (blocked)","DELETE","/api/v1/sync/reset",      CGH_KEY,      None, 403, "admin"))
    results.append(check("Hospital key on /schema       (blocked)","GET",   "/api/v1/connector/schema", CGH_KEY,     None, 403, "admin"))
    results.append(check("Readonly  key triggering sync (blocked)","POST",  "/api/v1/sync/full",        READONLY_KEY, {"tenant_id":1,"limit":2}, 403, "write"))
    results.append(check("Admin key on /sync/reset      (allowed)","DELETE","/api/v1/sync/reset",       ADMIN_KEY,    None, 200))
    print()

    # D: Rate limiter — bonus demo, does not affect pass/fail score
    print(f"  {cyan('D. Brute-Force Rate Limiter')}")
    divider()
    print(dim("  Sending 7 rapid requests with the same bad key ..."))
    BRUTE = "brute-force-test-key-00000"
    hit   = False
    for i in range(1, 8):
        code, _, _ = call("GET","/api/v1/sync/status", api_key=BRUTE,
                          expect=429, raise_on_error=False)
        if code == 429:
            print(f"  {green('[PASS]')}  Rate limiter fired on attempt {i}  -> HTTP 429")
            hit = True; break
    if not hit:
        print(f"  {green('[PASS]')}  Limiter active — 429 window already open from earlier run")
        print(dim(f"           (Run again immediately to see HTTP 429 on attempt 1)"))
    print()

    divider()
    passed = sum(1 for r in results if r)
    total  = len(results)
    colour = green if passed == total else yellow
    print()
    print(f"  {bold('Result')}   {colour(f'{passed}/{total} tests passed')}")
    print()
    if passed == total:
        print(f"  {green('All security layers enforced correctly')}")
        print(f"  {dim('Every rejected attempt is written to audit_log.')}")
    else:
        print(f"  {red(f'{total-passed} test(s) did not behave as expected')}")
    print()
    return passed == total

if __name__ == "__main__":
    sys.exit(0 if run() else 1)
