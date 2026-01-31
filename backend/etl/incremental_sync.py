"""
Incremental Sync - CDC-driven synchronization
Syncs only changed records based on CDC change log
"""
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy import text
import sys
import os

# Fix imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from common.database import hospital_db_session, shared_db_session
from common.models import Patient, Encounter

# Import ETL pipeline
from pipeline import ETLPipeline

# Import CDC monitor
connector_path = os.path.join(backend_dir, 'connector')
sys.path.insert(0, connector_path)

from cdc_monitor import CDCMonitor


class IncrementalSync:
    """
    Incremental synchronization based on CDC changes
    """
    
    def __init__(self, tenant_id: int = 1):
        """
        Initialize incremental sync
        
        Args:
            tenant_id: Hospital tenant ID
        """
        self.tenant_id = tenant_id
        self.pipeline = ETLPipeline(tenant_id)
        self.cdc_monitor = CDCMonitor(
            "postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db"
        )
    
    def get_changes_since_last_sync(self, last_sync_id: Optional[int] = None) -> List[Dict]:
        """
        Get all changes since last sync
        
        Args:
            last_sync_id: Last processed change ID
            
        Returns:
            List of change records
        """
        with hospital_db_session() as db:
            if last_sync_id:
                query = text("""
                    SELECT change_id, table_name, operation, record_id, changed_at
                    FROM data_change_log
                    WHERE change_id > :last_sync_id
                    ORDER BY change_id ASC
                """)
                result = db.execute(query, {"last_sync_id": last_sync_id})
            else:
                query = text("""
                    SELECT change_id, table_name, operation, record_id, changed_at
                    FROM data_change_log
                    ORDER BY change_id ASC
                """)
                result = db.execute(query)
            
            changes = []
            for row in result:
                changes.append({
                    'change_id': row[0],
                    'table_name': row[1],
                    'operation': row[2],
                    'record_id': row[3],
                    'changed_at': row[4]
                })
            
            return changes
    
    def sync_changed_patient(self, patient_id: int, operation: str) -> bool:
        """
        Sync a single changed patient
        
        Args:
            patient_id: Patient ID
            operation: INSERT, UPDATE, or DELETE
            
        Returns:
            Success status
        """
        try:
            if operation == 'DELETE':
                # Handle deletion in shared DB
                with shared_db_session() as shared_db:
                    delete_query = text("""
                        DELETE FROM fhir_patient
                        WHERE tenant_id = :tenant_id 
                        AND source_patient_id = :source_patient_id
                    """)
                    shared_db.execute(delete_query, {
                        'tenant_id': self.tenant_id,
                        'source_patient_id': str(patient_id)
                    })
                    shared_db.commit()
                print(f"  Deleted patient {patient_id}")
                return True
            
            # For INSERT or UPDATE
            with hospital_db_session() as hospital_db:
                patient = hospital_db.query(Patient).filter(
                    Patient.patient_id == patient_id
                ).first()
                
                if not patient:
                    print(f"  Patient {patient_id} not found")
                    return False
                
                # Transform and load
                fhir_patient = self.pipeline.mapping_service.map_patient_to_fhir(patient)
                
                with shared_db_session() as shared_db:
                    self.pipeline.load_patients(shared_db, [fhir_patient])
                
                print(f"  Synced patient {patient_id} ({operation})")
                return True
                
        except Exception as e:
            print(f"  Error syncing patient {patient_id}: {e}")
            return False
    
    def sync_changed_encounter(self, encounter_id: int, operation: str) -> bool:
        """
        Sync a single changed encounter
        
        Args:
            encounter_id: Encounter ID
            operation: INSERT, UPDATE, or DELETE
            
        Returns:
            Success status
        """
        try:
            if operation == 'DELETE':
                with shared_db_session() as shared_db:
                    delete_query = text("""
                        DELETE FROM fhir_encounter
                        WHERE tenant_id = :tenant_id 
                        AND source_encounter_id = :source_encounter_id
                    """)
                    shared_db.execute(delete_query, {
                        'tenant_id': self.tenant_id,
                        'source_encounter_id': str(encounter_id)
                    })
                    shared_db.commit()
                print(f"  Deleted encounter {encounter_id}")
                return True
            
            with hospital_db_session() as hospital_db:
                encounter = hospital_db.query(Encounter).filter(
                    Encounter.encounter_id == encounter_id
                ).first()
                
                if not encounter:
                    print(f"  Encounter {encounter_id} not found")
                    return False
                
                fhir_encounter = self.pipeline.mapping_service.map_encounter_to_fhir(encounter)
                
                with shared_db_session() as shared_db:
                    self.pipeline._load_encounters(shared_db, [fhir_encounter])
                
                print(f"  Synced encounter {encounter_id} ({operation})")
                return True
                
        except Exception as e:
            print(f"  Error syncing encounter {encounter_id}: {e}")
            return False
    
    def sync_incremental(self, last_sync_id: Optional[int] = None) -> Dict:
        """
        Perform incremental sync based on CDC changes
        
        Args:
            last_sync_id: Last processed change ID
            
        Returns:
            Sync statistics
        """
        print("\n" + "=" * 60)
        print("INCREMENTAL SYNC (CDC-Driven)")
        print("=" * 60)
        print(f"Tenant ID: {self.tenant_id}")
        print(f"Last Sync ID: {last_sync_id if last_sync_id else 'None (full sync)'}")
        
        # Get changes
        changes = self.get_changes_since_last_sync(last_sync_id)
        
        if not changes:
            print("\nNo changes to sync")
            return {
                'total_changes': 0,
                'synced': 0,
                'errors': 0,
                'last_change_id': last_sync_id
            }
        
        print(f"\nFound {len(changes)} changes to sync")
        print("-" * 60)
        
        stats = {
            'total_changes': len(changes),
            'synced': 0,
            'errors': 0,
            'by_table': {},
            'by_operation': {}
        }
        
        # Process each change
        for change in changes:
            table_name = change['table_name']
            operation = change['operation']
            record_id = change['record_id']
            
            # Track by table and operation
            stats['by_table'][table_name] = stats['by_table'].get(table_name, 0) + 1
            stats['by_operation'][operation] = stats['by_operation'].get(operation, 0) + 1
            
            # Sync based on table
            success = False
            if table_name == 'patients':
                success = self.sync_changed_patient(record_id, operation)
            elif table_name == 'encounters':
                success = self.sync_changed_encounter(record_id, operation)
            # Add more tables as needed
            
            if success:
                stats['synced'] += 1
            else:
                stats['errors'] += 1
            
            stats['last_change_id'] = change['change_id']
        
        # Print summary
        print("-" * 60)
        print(f"\nSync Summary:")
        print(f"  Total Changes: {stats['total_changes']}")
        print(f"  Successfully Synced: {stats['synced']}")
        print(f"  Errors: {stats['errors']}")
        print(f"  Last Change ID: {stats['last_change_id']}")
        
        print(f"\nBy Table:")
        for table, count in stats['by_table'].items():
            print(f"  {table}: {count}")
        
        print(f"\nBy Operation:")
        for operation, count in stats['by_operation'].items():
            print(f"  {operation}: {count}")
        
        return stats


if __name__ == "__main__":
    # Test incremental sync
    print("Testing Incremental Sync")
    
    sync = IncrementalSync(tenant_id=1)
    
    # Perform incremental sync
    stats = sync.sync_incremental()
    
    print("\n[OK] Incremental sync test complete")
