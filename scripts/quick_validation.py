"""Quick validation script"""
import sys
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')

from common.database import hospital_db_session, shared_db_session
from common.models import Patient, Encounter
from sqlalchemy import text

print("=" * 70)
print("CareLock Sync - Quick Validation")
print("=" * 70)

# Test 1: Hospital Database
print("\n[1] Hospital Database:")
with hospital_db_session() as db:
    patients = db.query(Patient).count()
    encounters = db.query(Encounter).count()
    print(f"  Patients: {patients}")
    print(f"  Encounters: {encounters}")

# Test 2: Shared Database
print("\n[2] Shared FHIR Database:")
with shared_db_session() as db:
    fhir_patients = db.execute(text("SELECT COUNT(*) FROM fhir_patient")).scalar()
    fhir_encounters = db.execute(text("SELECT COUNT(*) FROM fhir_encounter")).scalar()
    print(f"  FHIR Patients: {fhir_patients}")
    print(f"  FHIR Encounters: {fhir_encounters}")

# Test 3: CDC
print("\n[3] Change Data Capture:")
with hospital_db_session() as db:
    changes = db.execute(text("SELECT COUNT(*) FROM data_change_log")).scalar()
    print(f"  Changes Captured: {changes}")

print("\n" + "=" * 70)
print("✓ Validation Complete")
print("=" * 70)
