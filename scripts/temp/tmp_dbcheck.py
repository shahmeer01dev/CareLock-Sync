import sys, os, psycopg2
from dotenv import load_dotenv
load_dotenv(r"C:\Projects\CareLock-Sync\config\.env")

results = []

for label, host, port, db, user, pw in [
    ("hospital_db", os.getenv("HOSPITAL_DB_HOST","localhost"), int(os.getenv("HOSPITAL_DB_PORT",5432)),
     os.getenv("HOSPITAL_DB_NAME","hospital_db"), os.getenv("HOSPITAL_DB_USER","hospital_user"),
     os.getenv("HOSPITAL_DB_PASSWORD","hospital_pass")),
    ("shared_db",   os.getenv("SHARED_DB_HOST","localhost"), int(os.getenv("SHARED_DB_PORT",5433)),
     os.getenv("SHARED_DB_NAME","carelock_shared"), os.getenv("SHARED_DB_USER","shared_user"),
     os.getenv("SHARED_DB_PASSWORD","shared_pass")),
]:
    try:
        c = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pw, connect_timeout=5)
        cur = c.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
        tbls = [r[0] for r in cur.fetchall()]
        results.append(f"{label}: OK - tables={tbls}")
        c.close()
    except Exception as e:
        results.append(f"{label}: FAIL - {e}")

with open(r"C:\Projects\CareLock-Sync\tmp_out.txt","w") as f:
    f.write("\n".join(results))
