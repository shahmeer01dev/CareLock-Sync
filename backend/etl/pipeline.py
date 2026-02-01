"""
ETL Pipeline - Extract, Transform, Load
Synchronizes data from hospital database to FHIR shared database
"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import sys
import os

# Fix imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from common.database import hospital_db_session, shared_db_session
from common.models import Patient, Encounter, LabResult, Medication

# Import from schema-mapper
schema_mapper_path = os.path.join(backend_dir, 'schema-mapper')
sys.path.insert(0, schema_mapper_path)

from mapping_service import MappingService


class ETLPipeline:
    """
    ETL Pipeline for syncing hospital data to FHIR shared database
    """
    
    def __init__(self, tenant_id: int = 1):
        """
        Initialize ETL pipeline
        
        Args:
            tenant_id: Hospital tenant ID in shared database
        """
        self.tenant_id = tenant_id
        self.mapping_service = MappingService()
        self.stats = {
            'patients': {'extracted': 0, 'transformed': 0, 'loaded': 0, 'errors': 0},
            'encounters': {'extracted': 0, 'transformed': 0, 'loaded': 0, 'errors': 0},
            'observations': {'extracted': 0, 'transformed': 0, 'loaded': 0, 'errors': 0},
            'medications': {'extracted': 0, 'transformed': 0, 'loaded': 0, 'errors': 0}
        }
    
    def extract_patients(self, hospital_db: Session, limit: Optional[int] = None) -> List[Patient]:
        """
        Extract patients from hospital database
        
        Args:
            hospital_db: Hospital database session
            limit: Optional limit on number of records
            
        Returns:
            List of Patient model instances
        """
        query = hospital_db.query(Patient)
        if limit:
            query = query.limit(limit)
        
        patients = query.all()
        self.stats['patients']['extracted'] = len(patients)
        return patients
    
    def transform_patients(self, patients: List[Patient]) -> List[Dict]:
        """
        Transform patients to FHIR format
        
        Args:
            patients: List of Patient model instances
            
        Returns:
            List of FHIR Patient resources
        """
        fhir_patients = []
        for patient in patients:
            try:
                fhir_patient = self.mapping_service.map_patient_to_fhir(patient)
                fhir_patients.append(fhir_patient)
                self.stats['patients']['transformed'] += 1
            except Exception as e:
                print(f"Error transforming patient {patient.patient_id}: {e}")
                self.stats['patients']['errors'] += 1
        
        return fhir_patients
    
    def load_patients(self, shared_db: Session, fhir_patients: List[Dict]) -> int:
        """
        Load FHIR patients into shared database
        
        Args:
            shared_db: Shared database session
            fhir_patients: List of FHIR Patient resources
            
        Returns:
            Number of patients loaded
        """
        loaded_count = 0
        
        for fhir_patient in fhir_patients:
            try:
                # Insert into fhir_patient table
                insert_query = text("""
                    INSERT INTO fhir_patient (
                        tenant_id, source_patient_id, identifier_value,
                        family_name, given_name, gender, birth_date,
                        phone, email, address_line, address_city,
                        address_state, address_postal_code
                    ) VALUES (
                        :tenant_id, :source_patient_id, :identifier_value,
                        :family_name, :given_name, :gender, :birth_date,
                        :phone, :email, :address_line, :address_city,
                        :address_state, :address_postal_code
                    )
                    ON CONFLICT (tenant_id, source_patient_id) 
                    DO UPDATE SET
                        family_name = EXCLUDED.family_name,
                        given_name = EXCLUDED.given_name,
                        gender = EXCLUDED.gender,
                        birth_date = EXCLUDED.birth_date,
                        phone = EXCLUDED.phone,
                        email = EXCLUDED.email,
                        updated_at = CURRENT_TIMESTAMP
                """)
                
                # Extract data from FHIR resource
                name = fhir_patient.get('name', [{}])[0]
                telecom = fhir_patient.get('telecom', [])
                address = fhir_patient.get('address', [{}])[0]
                
                phone = telecom[0].get('value') if len(telecom) > 0 else None
                email = telecom[1].get('value') if len(telecom) > 1 else None
                
                params = {
                    'tenant_id': self.tenant_id,
                    'source_patient_id': fhir_patient.get('id'),
                    'identifier_value': fhir_patient.get('identifier', [{}])[0].get('value'),
                    'family_name': name.get('family'),
                    'given_name': name.get('given', []),
                    'gender': fhir_patient.get('gender'),
                    'birth_date': fhir_patient.get('birthDate'),
                    'phone': phone,
                    'email': email,
                    'address_line': address.get('line', []),
                    'address_city': address.get('city'),
                    'address_state': address.get('state'),
                    'address_postal_code': address.get('postalCode')
                }
                
                shared_db.execute(insert_query, params)
                loaded_count += 1
                self.stats['patients']['loaded'] += 1
                
            except Exception as e:
                print(f"Error loading patient {fhir_patient.get('id')}: {e}")
                self.stats['patients']['errors'] += 1
        
        shared_db.commit()
        return loaded_count
    
    def sync_patients(self, limit: Optional[int] = None) -> Dict:
        """
        Complete ETL process for patients
        
        Args:
            limit: Optional limit on number of records
            
        Returns:
            Statistics dictionary
        """
        print("\n" + "=" * 60)
        print("Syncing Patients")
        print("=" * 60)
        
        with hospital_db_session() as hospital_db:
            # Extract
            print("[1/3] Extracting patients from hospital database...")
            patients = self.extract_patients(hospital_db, limit)
            print(f"  Extracted: {len(patients)} patients")
            
            # Transform
            print("[2/3] Transforming to FHIR format...")
            fhir_patients = self.transform_patients(patients)
            print(f"  Transformed: {len(fhir_patients)} patients")
            
            # Load
            with shared_db_session() as shared_db:
                print("[3/3] Loading into shared database...")
                loaded = self.load_patients(shared_db, fhir_patients)
                print(f"  Loaded: {loaded} patients")
        
        return self.stats['patients']
    
    def sync_encounters(self, limit: Optional[int] = None) -> Dict:
        """
        Complete ETL process for encounters
        
        Args:
            limit: Optional limit on number of records
            
        Returns:
            Statistics dictionary
        """
        print("\n" + "=" * 60)
        print("Syncing Encounters")
        print("=" * 60)
        
        with hospital_db_session() as hospital_db:
            # Extract
            print("[1/3] Extracting encounters from hospital database...")
            query = hospital_db.query(Encounter)
            if limit:
                query = query.limit(limit)
            encounters = query.all()
            self.stats['encounters']['extracted'] = len(encounters)
            print(f"  Extracted: {len(encounters)} encounters")
            
            # Transform
            print("[2/3] Transforming to FHIR format...")
            fhir_encounters = []
            for encounter in encounters:
                try:
                    fhir_enc = self.mapping_service.map_encounter_to_fhir(encounter)
                    fhir_encounters.append(fhir_enc)
                    self.stats['encounters']['transformed'] += 1
                except Exception as e:
                    print(f"Error transforming encounter {encounter.encounter_id}: {e}")
                    self.stats['encounters']['errors'] += 1
            
            print(f"  Transformed: {len(fhir_encounters)} encounters")
            
            # Load
            with shared_db_session() as shared_db:
                print("[3/3] Loading into shared database...")
                loaded = self._load_encounters(shared_db, fhir_encounters)
                print(f"  Loaded: {loaded} encounters")
        
        return self.stats['encounters']
    
    def _load_encounters(self, shared_db: Session, fhir_encounters: List[Dict]) -> int:
        """Load FHIR encounters into shared database"""
        loaded_count = 0
        
        for fhir_enc in fhir_encounters:
            try:
                insert_query = text("""
                    INSERT INTO fhir_encounter (
                        tenant_id, source_encounter_id, patient_id,
                        class_code, status, period_start, period_end,
                        reason_display, diagnosis
                    ) 
                    SELECT 
                        :tenant_id, :source_encounter_id, fp.id,
                        :class_code, :status, :period_start, :period_end,
                        :reason_display, :diagnosis
                    FROM fhir_patient fp
                    WHERE fp.tenant_id = :tenant_id 
                    AND fp.source_patient_id = :source_patient_id
                    ON CONFLICT (tenant_id, source_encounter_id)
                    DO UPDATE SET
                        status = EXCLUDED.status,
                        period_end = EXCLUDED.period_end,
                        updated_at = CURRENT_TIMESTAMP
                """)
                
                # Extract patient reference
                subject_ref = fhir_enc.get('subject', {}).get('reference', '')
                source_patient_id = subject_ref.split('/')[-1] if '/' in subject_ref else None
                
                period = fhir_enc.get('period', {})
                reason = fhir_enc.get('reasonCode', [{}])[0]
                diagnosis_list = fhir_enc.get('diagnosis', [{}])
                
                params = {
                    'tenant_id': self.tenant_id,
                    'source_encounter_id': fhir_enc.get('id'),
                    'source_patient_id': source_patient_id,
                    'class_code': fhir_enc.get('class', {}).get('code'),
                    'status': fhir_enc.get('status'),
                    'period_start': period.get('start'),
                    'period_end': period.get('end'),
                    'reason_display': [reason.get('text')] if reason.get('text') else None,
                    'diagnosis': [d.get('condition', {}).get('display') for d in diagnosis_list]
                }
                
                shared_db.execute(insert_query, params)
                loaded_count += 1
                self.stats['encounters']['loaded'] += 1
                
            except Exception as e:
                print(f"Error loading encounter {fhir_enc.get('id')}: {e}")
                self.stats['encounters']['errors'] += 1
        
        shared_db.commit()
        return loaded_count
    
    def sync_all(self, limit: Optional[int] = None) -> Dict:
        """
        Sync all resource types
        
        Args:
            limit: Optional limit per resource type
            
        Returns:
            Complete statistics
        """
        print("\n" + "=" * 60)
        print("FULL ETL PIPELINE SYNC")
        print("=" * 60)
        print(f"Tenant ID: {self.tenant_id}")
        print(f"Limit per resource: {limit if limit else 'None'}")
        
        start_time = datetime.now()
        
        # Sync patients first (required for references)
        self.sync_patients(limit)
        
        # Sync encounters
        self.sync_encounters(limit)
        
        # Calculate totals
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print("SYNC COMPLETE")
        print("=" * 60)
        print(f"Duration: {duration:.2f} seconds")
        print(f"\nPatients:")
        print(f"  Extracted: {self.stats['patients']['extracted']}")
        print(f"  Transformed: {self.stats['patients']['transformed']}")
        print(f"  Loaded: {self.stats['patients']['loaded']}")
        print(f"  Errors: {self.stats['patients']['errors']}")
        print(f"\nEncounters:")
        print(f"  Extracted: {self.stats['encounters']['extracted']}")
        print(f"  Transformed: {self.stats['encounters']['transformed']}")
        print(f"  Loaded: {self.stats['encounters']['loaded']}")
        print(f"  Errors: {self.stats['encounters']['errors']}")
        
        return self.stats


if __name__ == "__main__":
    # Test ETL pipeline
    print("Testing ETL Pipeline")
    
    pipeline = ETLPipeline(tenant_id=1)
    
    # Sync small batch for testing
    stats = pipeline.sync_all(limit=10)
    
    print("\n[OK] ETL Pipeline test complete")
