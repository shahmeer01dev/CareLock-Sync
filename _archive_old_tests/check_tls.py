import sys
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
from common.config import settings
from common.database import shared_engine
from sqlalchemy import text

print('Shared DB URL:', settings.shared_db_url[:70], '...')

with shared_engine.connect() as conn:
    ssl_in_use = conn.execute(text("SELECT ssl_is_used()")).scalar()
    pg_ver     = conn.execute(text("SELECT version()")).scalar()
    print('SSL connection active:', ssl_in_use)
    print('PostgreSQL:', pg_ver[:65])
    row = conn.execute(text(
        "SELECT pg_ssl.ssl, pg_ssl.version FROM pg_stat_ssl "
        "JOIN pg_stat_activity ON pg_stat_ssl.pid = pg_stat_activity.pid "
        "WHERE pg_stat_activity.application_name = 'psycopg2' LIMIT 1"
    )).fetchone()
    if row:
        print(f'Connection TLS: ssl={row[0]} version={row[1]}')
print('TLS CHECK COMPLETE')
