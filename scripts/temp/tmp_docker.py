import subprocess, os
r1 = subprocess.run(["docker","ps","--format","table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
    capture_output=True, text=True)
r2 = subprocess.run(["docker-compose","-f",r"C:\Projects\CareLock-Sync\docker-compose.yml","ps"],
    capture_output=True, text=True, cwd=r"C:\Projects\CareLock-Sync")
with open(r"C:\Projects\CareLock-Sync\tmp_out.txt","w") as f:
    f.write("=== docker ps ===\n" + r1.stdout + r1.stderr)
    f.write("\n=== compose ps ===\n" + r2.stdout + r2.stderr)
