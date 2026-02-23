import sys
sys.path.insert(0, r"C:\Projects\CareLock-Sync\backend")
try:
    import psycopg2
    c = psycopg2.connect(host="localhost", port=5432, dbname="hospital_db",
                         user="hospital_user", password="hospital_pass", connect_timeout=5)
    cur = c.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1")
    tbls = [r[0] for r in cur.fetchall()]
    c.close()
    out = "hospital_db: OK tables=" + str(tbls)
except Exception as e:
    out = "hospital_db: FAIL " + str(e)

try:
    c2 = psycopg2.connect(host="localhost", port=5433, dbname="carelock_shared",
                          user="shared_user", password="shared_pass", connect_timeout=5)
    cur2 = c2.cursor()
    cur2.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1")
    tbls2 = [r[0] for r in cur2.fetchall()]
    c2.close()
    out2 = "shared_db: OK tables=" + str(tbls2)
except Exception as e:
    out2 = "shared_db: FAIL " + str(e)

print(out)
print(out2)
