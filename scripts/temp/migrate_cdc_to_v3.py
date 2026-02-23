"""
CDC v3 — Database Migration Script
Run this ONCE to upgrade from v2 to v3 schema.

Usage:
    python migrate_cdc_to_v3.py
"""
import os
import sys
from sqlalchemy import create_engine, text

# Add backend to path
ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)

def get_db_url():
    """Get database URL from environment or .env file."""
    url = os.getenv("TEST_DB_URL") or os.getenv("HOSPITAL_DB_URL")
    if url:
        return url
    
    # Try loading from .env
    env_file = os.path.join(ROOT, ".env")
    if os.path.exists(env_file):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            return os.getenv("HOSPITAL_DB_URL", "postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db")
        except ImportError:
            pass
    
    return "postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db"

def migrate():
    """Migrate database from v2 to v3 schema."""
    print("\n" + "="*70)
    print("  CDC v3 — Database Migration")
    print("="*70)
    
    db_url = get_db_url()
    print(f"\nDatabase: {db_url.split('@')[1] if '@' in db_url else db_url}")
    
    engine = create_engine(db_url, pool_pre_ping=True)
    
    print("\n[Step 1/3] Checking existing schema...")
    with engine.connect() as conn:
        # Check if data_change_log exists
        result = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'data_change_log'
            )
        """)).scalar()
        
        if result:
            print("  ✓ data_change_log exists (v2 schema)")
            
            # Check record_id type
            record_id_type = conn.execute(text("""
                SELECT data_type FROM information_schema.columns
                WHERE table_name = 'data_change_log'
                AND column_name = 'record_id'
                AND table_schema = 'public'
            """)).scalar()
            
            print(f"  • record_id type: {record_id_type}")
            
            # Check if user_name exists
            has_user_name = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'data_change_log'
                    AND column_name = 'user_name'
                    AND table_schema = 'public'
                )
            """)).scalar()
            
            print(f"  • user_name column: {'exists' if has_user_name else 'MISSING'}")
            
            if record_id_type == 'integer' or not has_user_name:
                print("\n  ⚠ Schema needs migration to v3")
                choice = input("\n  Drop and recreate table? (all data will be lost) [y/N]: ")
                
                if choice.lower() != 'y':
                    print("\n  Migration cancelled.")
                    print("\n  To migrate existing data, run:")
                    print("    from connector.cdc_monitor import CDCMonitor")
                    print("    m = CDCMonitor('your_db_url')")
                    print("    m.migrate_schema()")
                    return
        else:
            print("  • data_change_log does not exist (fresh install)")
    
    print("\n[Step 2/3] Dropping old schema...")
    with engine.connect() as conn:
        # Drop old table and related objects
        conn.execute(text("DROP TABLE IF EXISTS data_change_log CASCADE"))
        conn.execute(text("DROP FUNCTION IF EXISTS log_data_change() CASCADE"))
        conn.execute(text("DROP FUNCTION IF EXISTS log_table_changes() CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS _cdc_config CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS cdc_watermarks CASCADE"))
        conn.commit()
        print("  ✓ Old schema dropped")
    
    print("\n[Step 3/3] Creating v3 schema...")
    from connector.cdc_monitor import CDCMonitor
    
    monitor = CDCMonitor(db_url)
    monitor.configure_tenant(tenant_id=42)  # Test tenant
    monitor.create_change_log_table()
    monitor.create_trigger_function()
    
    print("  ✓ v3 schema created")
    
    # Verify
    with engine.connect() as conn:
        record_id_type = conn.execute(text("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name = 'data_change_log'
            AND column_name = 'record_id'
        """)).scalar()
        
        has_user_name = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'data_change_log'
                AND column_name = 'user_name'
            )
        """)).scalar()
        
        has_tenant_id = conn.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'data_change_log'
                AND column_name = 'tenant_id'
            )
        """)).scalar()
    
    print("\n" + "="*70)
    print("  Verification:")
    print("="*70)
    print(f"  record_id type:    {record_id_type}  {'✓' if record_id_type in ('text', 'character varying') else '✗'}")
    print(f"  user_name column:  {'present' if has_user_name else 'MISSING'}  {'✓' if has_user_name else '✗'}")
    print(f"  tenant_id column:  {'present' if has_tenant_id else 'MISSING'}  {'✓' if has_tenant_id else '✗'}")
    
    if record_id_type in ('text', 'character varying') and has_user_name and has_tenant_id:
        print("\n  ✓✓✓ Migration successful! ✓✓✓")
        print("\n  Now run: RUN_CDC_V3_TESTS.bat")
    else:
        print("\n  ✗ Migration incomplete. Check errors above.")
    
    print("="*70)
    
    engine.dispose()

if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
