"""
Test incremental CDC functionality
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from sqlalchemy import create_engine, text
from datetime import datetime


def test_incremental_cdc():
    """Test incremental CDC step by step"""
    
    print("=" * 80)
    print("INCREMENTAL CDC DEBUG TEST")
    print("=" * 80)
    
    # Database connections
    hospital_db_url = "postgresql://postgres:postgres@localhost:5432/hospital_db"
    shared_db_url = "postgresql://postgres:postgres@localhost:5433/carelock_shared"
    
    hospital_engine = create_engine(hospital_db_url)
    shared_engine = create_engine(shared_db_url)
    
    # Step 1: Check CDC trigger exists
    print("\n[STEP 1] Checking CDC trigger on patients table...")
    with hospital_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT trigger_name, event_manipulation
            FROM information_schema.triggers
            WHERE event_object_table = 'patients'
        """))
        triggers = result.fetchall()
        
        if triggers:
            print(f"✓ Found {len(triggers)} trigger(s):")
            for trigger in triggers:
                print(f"  - {trigger[0]} ({trigger[1]})")
        else:
            print("✗ NO CDC TRIGGERS FOUND!")
            print("  Run: python scripts/setup_cdc.py")
            return
    
    # Step 2: Check data_change_log table
    print("\n[STEP 2] Checking data_change_log table...")
    with hospital_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) as total,
                   MAX(change_id) as max_id,
                   MIN(change_id) as min_id
            FROM data_change_log
        """))
        row = result.fetchone()
        
        print(f"  Total changes: {row[0]}")
        print(f"  Change ID range: {row[2]} - {row[1]}")
        
        if row[0] == 0:
            print("  WARNING: No changes in log. Make some changes first!")
    
    # Step 3: Get recent changes
    print("\n[STEP 3] Getting last 5 changes...")
    with hospital_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT change_id, table_name, operation, record_id, changed_at
            FROM data_change_log
            ORDER BY change_id DESC
            LIMIT 5
        """))
        
        changes = result.fetchall()
        if changes:
            print(f"  Found {len(changes)} recent changes:")
            for change in changes:
                print(f"    ID {change[0]}: {change[2]} on {change[1]} (record {change[3]}) at {change[4]}")
        else:
            print("  No changes found")
    
    # Step 4: Make a test change
    print("\n[STEP 4] Making a test change (UPDATE patient_id=1)...")
    try:
        with hospital_engine.connect() as conn:
            # Get current data
            result = conn.execute(text("SELECT first_name FROM patients WHERE patient_id = 1"))
            current = result.fetchone()
            
            if current:
                print(f"  Current first_name: {current[0]}")
                
                # Update
                conn.execute(text("""
                    UPDATE patients 
                    SET first_name = 'TestUpdate_' || first_name
                    WHERE patient_id = 1
                    AND first_name NOT LIKE 'TestUpdate_%'
                """))
                conn.commit()
                
                # Check if change was logged
                result = conn.execute(text("""
                    SELECT change_id, operation, new_data->>'first_name' as new_name
                    FROM data_change_log
                    WHERE table_name = 'patients' 
                    AND record_id = 1
                    ORDER BY change_id DESC
                    LIMIT 1
                """))
                
                logged = result.fetchone()
                if logged:
                    print(f"  ✓ Change logged: ID {logged[0]}, {logged[1]}, new name: {logged[2]}")
                else:
                    print("  ✗ Change NOT logged!")
            else:
                print("  No patient with ID=1 found")
                
    except Exception as e:
        print(f"  ERROR: {e}")
    
    # Step 5: Test IncrementalSync class
    print("\n[STEP 5] Testing IncrementalSync class...")
    try:
        from etl.incremental_sync import IncrementalSync
        
        sync = IncrementalSync(tenant_id=1)
        
        # Get last change ID
        with hospital_engine.connect() as conn:
            result = conn.execute(text("SELECT MAX(change_id) FROM data_change_log"))
            max_change_id = result.scalar()
            
            print(f"  Max change ID in log: {max_change_id}")
            
            # Try syncing from 0 (should get all changes)
            print(f"\n  Running incremental sync from change_id=0...")
            stats = sync.sync_incremental(last_sync_id=0)
            
            print(f"\n  Sync stats:")
            print(f"    Total changes: {stats['total_changes']}")
            print(f"    Synced: {stats['synced']}")
            print(f"    Errors: {stats['errors']}")
            print(f"    Last change ID: {stats['last_change_id']}")
            
            if stats['synced'] > 0:
                print("  ✓ Incremental sync WORKING!")
            else:
                print("  ✗ Incremental sync processed 0 changes")
                
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 6: Verify data in shared DB
    print("\n[STEP 6] Checking FHIR data in shared database...")
    with shared_engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) as total
            FROM fhir_patient
            WHERE tenant_id = 1
        """))
        count = result.scalar()
        print(f"  Total FHIR patients: {count}")
        
        if count > 0:
            result = conn.execute(text("""
                SELECT fhir_id, source_patient_id, resource->'name'->0->>'text' as name
                FROM fhir_patient
                WHERE tenant_id = 1
                ORDER BY fhir_id DESC
                LIMIT 3
            """))
            
            print(f"  Recent patients:")
            for row in result:
                print(f"    {row[0]}: Patient {row[1]} - {row[2]}")
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    test_incremental_cdc()
