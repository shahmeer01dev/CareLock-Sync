"""
Test database connections and verify data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2

# Database configurations
HOSPITAL_DB = "postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db"
SHARED_DB = "postgresql://shared_user:shared_pass@localhost:5433/carelock_shared"


def test_hospital_db():
    """Test connection to hospital database and display sample data"""
    print("\n" + "=" * 60)
    print("Testing Hospital Database Connection")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(HOSPITAL_DB)
        cursor = conn.cursor()
        
        # Test patients table
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        print(f"\n[OK] Connected to Hospital Database")
        print(f"Total Patients: {patient_count}")
        
        # Get sample patient data
        cursor.execute("""
            SELECT patient_id, first_name, last_name, medical_record_number, 
                   gender, blood_type, date_of_birth
            FROM patients 
            LIMIT 5
        """)
        
        print("\nSample Patients:")
        print("-" * 60)
        for row in cursor.fetchall():
            print(f"ID: {row[0]} | {row[1]} {row[2]} | MRN: {row[3]} | {row[4]} | {row[5]} | DOB: {row[6]}")
        
        # Test encounters
        cursor.execute("SELECT COUNT(*) FROM encounters")
        encounter_count = cursor.fetchone()[0]
        print(f"\nTotal Encounters: {encounter_count}")
        
        # Test lab results
        cursor.execute("SELECT COUNT(*) FROM lab_results")
        lab_count = cursor.fetchone()[0]
        print(f"Total Lab Results: {lab_count}")
        
        # Test medications
        cursor.execute("SELECT COUNT(*) FROM medications")
        med_count = cursor.fetchone()[0]
        print(f"Total Medications: {med_count}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def test_shared_db():
    """Test connection to shared central database"""
    print("\n" + "=" * 60)
    print("Testing Shared Central Database Connection")
    print("=" * 60)
    
    try:
        conn = psycopg2.connect(SHARED_DB)
        cursor = conn.cursor()
        
        print(f"\n[OK] Connected to Shared Database")
        
        # Test hospital tenants table
        cursor.execute("SELECT * FROM hospital_tenants")
        tenants = cursor.fetchall()
        print(f"\nRegistered Hospital Tenants: {len(tenants)}")
        print("-" * 60)
        for tenant in tenants:
            print(f"ID: {tenant[0]} | {tenant[1]} | Code: {tenant[2]} | Active: {tenant[6]}")
        
        # Test FHIR tables
        cursor.execute("SELECT COUNT(*) FROM fhir_patient")
        patient_count = cursor.fetchone()[0]
        print(f"\nFHIR Patients: {patient_count}")
        
        cursor.execute("SELECT COUNT(*) FROM fhir_encounter")
        encounter_count = cursor.fetchone()[0]
        print(f"FHIR Encounters: {encounter_count}")
        
        cursor.execute("SELECT COUNT(*) FROM fhir_observation")
        obs_count = cursor.fetchone()[0]
        print(f"FHIR Observations: {obs_count}")
        
        cursor.execute("SELECT COUNT(*) FROM fhir_medication_request")
        med_count = cursor.fetchone()[0]
        print(f"FHIR Medication Requests: {med_count}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def main():
    print("\n" + "=" * 60)
    print("CareLock Sync - Database Verification")
    print("=" * 60)
    
    # Test both databases
    hospital_ok = test_hospital_db()
    shared_ok = test_shared_db()
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    print(f"Hospital Database: {'[OK]' if hospital_ok else '[FAILED]'}")
    print(f"Shared Database: {'[OK]' if shared_ok else '[FAILED]'}")
    
    if hospital_ok and shared_ok:
        print("\n*** All database connections successful! ***")
        print("\nNext Steps:")
        print("1. Access pgAdmin at http://localhost:5050")
        print("   Login: admin@carelock.com / admin123")
        print("2. Explore the data in both databases")
        print("3. Start Phase 1, Step 3: Core Project Architecture")
        return 0
    else:
        print("\n*** Some database connections failed ***")
        return 1


if __name__ == "__main__":
    sys.exit(main())
