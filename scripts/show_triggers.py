import sys
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
from common.database import hospital_db_session
from sqlalchemy import text

with hospital_db_session() as db:
    # Which tables have triggers?
    rows = db.execute(text(
        "SELECT trigger_name, event_object_table, event_manipulation "
        "FROM information_schema.triggers "
        "WHERE trigger_schema = 'public' "
        "ORDER BY event_object_table"
    )).fetchall()
    print("=== TRIGGERS ===")
    for r in rows:
        print(f"  trigger={r[0]:45} table={r[1]:20} event={r[2]}")

    # Show the trigger function source — this is the key piece
    print()
    print("=== TRIGGER FUNCTION BODY ===")
    src = db.execute(text(
        "SELECT pg_get_functiondef(oid) FROM pg_proc WHERE proname = 'log_table_changes'"
    )).scalar()
    print(src)
