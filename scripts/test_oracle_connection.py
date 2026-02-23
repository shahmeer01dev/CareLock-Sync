"""Test Oracle Connection"""
import cx_Oracle

print("=" * 80)
print("Oracle Connection Test")
print("=" * 80)

try:
    # Try connecting as SYSTEM user first
    print("\n[1/3] Testing connection to Oracle XE...")
    
    # DSN for Oracle XE
    dsn = cx_Oracle.makedsn('localhost', 1521, service_name='XE')
    
    print(f"  DSN: {dsn}")
    print(f"  Connecting as SYSTEM...")
    
    connection = cx_Oracle.connect(
        user='system',
        password='OraclePass123',
        dsn=dsn,
        encoding='UTF-8'
    )
    
    print("  [OK] Connected to Oracle XE!")
    
    cursor = connection.cursor()
    
    print("\n[2/3] Checking Oracle version...")
    cursor.execute("SELECT banner FROM v$version WHERE banner LIKE 'Oracle%'")
    version = cursor.fetchone()[0]
    print(f"  {version}")
    
    print("\n[3/3] Checking available tablespaces...")
    cursor.execute("SELECT tablespace_name FROM dba_tablespaces")
    tablespaces = cursor.fetchall()
    print(f"  Found {len(tablespaces)} tablespaces:")
    for ts in tablespaces[:5]:
        print(f"    - {ts[0]}")
    
    print("\n" + "=" * 80)
    print("Oracle Connection: SUCCESS!")
    print("=" * 80)
    
    cursor.close()
    connection.close()
    
except cx_Oracle.DatabaseError as e:
    error, = e.args
    print(f"\n[ERROR] Database error: {error.message}")
    print(f"  Code: {error.code}")
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
