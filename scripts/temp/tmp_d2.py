import subprocess
r = subprocess.run(["docker","ps"], capture_output=True, text=True)
with open(r"C:\Projects\CareLock-Sync\tmp_out.txt","w") as f:
    f.write(r.stdout + r.stderr)
