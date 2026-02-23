import os, ast, sys

ROOT = r"C:\Projects\CareLock-Sync\backend"
issues = []
ok_files = []

for dirpath, dirs, files in os.walk(ROOT):
    dirs[:] = [d for d in dirs if d not in ("__pycache__","venv",".git")]
    for fn in files:
        if not fn.endswith(".py"): continue
        full = os.path.join(dirpath, fn)
        rel  = full.replace(ROOT+"\\","")
        try:
            src = open(full, encoding="utf-8", errors="replace").read()
            ast.parse(src)
            ok_files.append(rel)
        except SyntaxError as e:
            issues.append(f"SYNTAX {rel}: {e}")
        except Exception as e:
            issues.append(f"ERROR  {rel}: {e}")

lines = [f"=== Python AST Check ({len(ok_files)} OK, {len(issues)} FAIL) ==="]
if issues:
    lines += issues
else:
    lines.append("All files parse cleanly.")
lines.append("")
lines.append("=== Backend source files ===")
lines += ok_files

with open(r"C:\Projects\CareLock-Sync\tmp_out.txt","w") as f:
    f.write("\n".join(lines))
