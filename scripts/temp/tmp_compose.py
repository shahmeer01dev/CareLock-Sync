import subprocess, sys
r = subprocess.run(
    ["docker-compose", "-f", r"C:\Projects\CareLock-Sync\docker-compose.yml", "up", "-d", "--remove-orphans"],
    capture_output=True, text=True, cwd=r"C:\Projects\CareLock-Sync"
)
with open(r"C:\Projects\CareLock-Sync\tmp_out.txt","w") as f:
    f.write("STDOUT:\n" + r.stdout + "\nSTDERR:\n" + r.stderr + "\nRC:" + str(r.returncode))
