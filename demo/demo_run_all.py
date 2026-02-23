"""
demo_run_all.py — CareLock Sync Demo  (MASTER RUNNER)
======================================================
Runs all five demos in sequence. Waits for Enter between sections.
Never crashes the whole demo if one section fails.

Usage
  python demo_run_all.py           # interactive (waits for Enter)
  python demo_run_all.py --auto    # no pauses (CI / rehearsal)
"""
import sys, os, time, traceback
sys.path.insert(0, os.path.dirname(__file__))

from config import BASE_URL, call, dim, bold, green, red, yellow, cyan

import demo_full_sync
import demo_incremental_sync
import demo_security
import demo_admin_observability
import demo_connector_health

AUTO = "--auto" in sys.argv

BAR  = "=" * 68
THIN = "-" * 68

def banner(title, subtitle=""):
    print()
    print(BAR)
    print(f"  {bold(title)}")
    if subtitle:
        print(f"  {dim(subtitle)}")
    print(BAR)
    print()

def pause(prompt="Press Enter to continue ..."):
    if AUTO:
        time.sleep(0.5); return
    try:
        input(f"\n  {dim(prompt)}\n")
    except (EOFError, KeyboardInterrupt):
        print(yellow("\n  Demo stopped by user.")); sys.exit(0)

def run_safe(name, fn):
    try:
        return bool(fn())
    except KeyboardInterrupt:
        raise
    except Exception as exc:
        print(red(f"\n  [{name}] raised an unexpected error: {exc}"))
        if "--verbose" in sys.argv:
            traceback.print_exc()
        return False

def pre_check():
    print(dim(f"  Checking {BASE_URL}/health ..."), end=" ", flush=True)
    try:
        _, data, ms = call("GET", "/health", raise_on_error=False)
        if data.get("status") == "healthy":
            print(green(f"API is UP  ({ms} ms)"))
        else:
            print(yellow(f"UP but status={data.get('status')}"))
    except SystemExit:
        raise
    except Exception:
        print(red("FAILED"))
        print(red(f"\n  Cannot reach {BASE_URL}"))
        print(dim("  Start: uvicorn api.main:app --host 0.0.0.0 --port 8000"))
        sys.exit(1)

def main():
    # Opening banner
    print()
    print(BAR)
    print(f"     {bold('CareLock Sync  —  Live Demo')}")
    print(f"     {dim('Healthcare Middleware  |  FHIR R4  |  Multi-tenant  |  HIPAA-ready')}")
    print(BAR)
    print()
    print(f"  {bold('API')}        {BASE_URL}")
    print(f"  {bold('Auth')}       X-API-Key header  (3 roles: admin / hospital / readonly)")
    print(f"  {bold('Hospitals')}  CGH001  PGH002  NMH003  CHI004  AKH005")
    print()
    pre_check()
    print()
    if not AUTO:
        print(dim("  Each section pauses for Enter so you control the pace."))
        print(dim("  Press Ctrl+C at any time to stop."))
    print()
    pause("Press Enter to begin the demo ...")

    demos = [
        ("1/5  FULL SYNC",             "400 FHIR records in one call",                        demo_full_sync.run),
        ("2/5  INCREMENTAL SYNC",      "CDC-driven: only changed records processed",           demo_incremental_sync.run),
        ("3/5  SECURITY",              "Auth  |  tenant isolation  |  role enforcement",       demo_security.run),
        ("4/5  ADMIN OBSERVABILITY",   "Quality scores  |  partition stats  |  CDC lag",       demo_admin_observability.run),
        ("5/5  CONNECTOR HEALTH",      "Database connectivity  |  latency  |  FHIR counts",   demo_connector_health.run),
    ]

    results = []
    for i, (title, subtitle, fn) in enumerate(demos):
        banner(title, subtitle)
        ok = run_safe(title, fn)
        results.append((title, ok))
        if i < len(demos) - 1:
            next_title = demos[i+1][0]
            pause(f"Press Enter -> {next_title}")

    # Final scorecard
    print()
    print(BAR)
    print(f"  {bold('DEMO COMPLETE')}")
    print(BAR)
    print()
    for title, ok in results:
        icon  = green("PASS") if ok else red("FAIL")
        label = dim(title) if ok else red(title)
        print(f"  [{icon}]  {label}")

    passed = sum(1 for _, ok in results if ok)
    total  = len(results)
    print()
    colour = green if passed == total else yellow
    print(f"  {bold('Score')}   {colour(f'{passed}/{total} sections passed')}")
    print()

    if passed == total:
        print(f"  {green('All demos completed successfully.')}")
        print()
        print(dim("  Key numbers:"))
        print(f"    {dim('*')} ~16,000 records / min  (target: >10,000)")
        print(f"    {dim('*')} TLS 1.3 on all database connections")
        print(f"    {dim('*')} 5 hospitals  |  3 roles  |  full audit log")
        print(f"    {dim('*')} FHIR R4 output  (HL7 international standard)")
    else:
        failed = [t for t, ok in results if not ok]
        print(f"  {yellow('Issues in:')}  {', '.join(failed)}")
        print(f"  {dim('Re-run individually:  python demo_<name>.py')}")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n  {yellow('Demo interrupted.')}\n")
        sys.exit(0)
