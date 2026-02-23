import sys, os
pkgs = ["cryptography","psycopg2","sqlalchemy","fastapi","pydantic","faker","dotenv","pytest"]
lines = []
for p in pkgs:
    try:
        m = __import__(p)
        v = getattr(m, "__version__", "?")
        lines.append(f"OK  {p} {v}")
    except ImportError as e:
        lines.append(f"MISS {p} {e}")
with open(r"C:\Projects\CareLock-Sync\tmp_out.txt","w") as f:
    f.write("\n".join(lines))
print("done")
