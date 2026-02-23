
"""One-time bootstrap: reads files baked into this script and writes them to demo/."""
import os, sys

DEMO_DIR = os.path.dirname(os.path.abspath(__file__))

# All file contents are embedded below as raw strings so the copy works
# even when the container filesystem is not reachable from Windows.

FILES = {}  # populated below

# ─────────────────────────────────────────────────────────────
FILES["_DONE"] = "1"   # sentinel

for name, content in FILES.items():
    if name.startswith("_"):
        continue
    path = os.path.join(DEMO_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  Wrote {name}  ({len(content)} chars)")

print("Done.")
