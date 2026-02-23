import importlib, json

pkgs = ["chromadb", "requests", "fastapi", "uvicorn", "sqlalchemy", "pydantic"]
results = {}
for pkg in pkgs:
    try:
        m = importlib.import_module(pkg)
        ver = getattr(m, "__version__", "?")
        results[pkg] = ver
    except ImportError:
        results[pkg] = "NOT INSTALLED"

out = ""
for k, v in results.items():
    out += f"{k}: {v}\n"

with open(r"C:\Projects\CareLock-Sync\scripts\tmp\pkgs.txt", "w") as f:
    f.write(out)
