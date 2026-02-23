"""Setup MongoDB Database with Sample Data"""
from pymongo import MongoClient
from faker import Faker
import random
from datetime import datetime

fake = Faker()
print("=" * 80)
print("MongoDB Database Setup - Docker")
print("=" * 80)

try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['hospital_db_mongodb']
    
    print("\n[1/6] Dropping existing collections...")
    db.patients.drop()
    db.encounters.drop()
    db.lab_results.drop()
    db.medications.drop()
    db.change_log.drop()
    print("  [OK] Collections dropped")
    
    print("\n[2/6] Creating indexes...")
    db.patients.create_index("medical_record_number", unique=True)
    db.encounters.create_index("patient_id")
    db.lab_results.create_index("encounter_id")
    db.medications.create_index("encounter_id")
    print("  [OK] Indexes created")
    
    print("\n[3/6] Inserting patients...")
    patients = []
    for i in range(100):
        patients.append({
            'medical_record_number': f'MRN-MONGO-{i+1:05d}',
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=90),
            'gender': random.choice(['male', 'female']),
            'email': fake.email(),
            'created_at': datetime.utcnow()
        })
    result = db.patients.insert_many(patients)
    patient_ids = result.inserted_ids
    print(f"  [OK] Inserted {len(patient_ids)} patients")
    
    print("\n[4/6] Inserting encounters...")
    encounters = []
    for i in range(200):
        encounters.append({
            'patient_id': random.choice(patient_ids),
            'encounter_type': random.choice(['Emergency', 'Outpatient', 'Inpatient']),
            'admission_date': fake.date_time_between(start_date='-1y'),
            'status': 'finished',
            'created_at': datetime.utcnow()
        })
    result = db.encounters.insert_many(encounters)
    encounter_ids = result.inserted_ids
    print(f"  [OK] Inserted {len(encounter_ids)} encounters")
    
    print("\n[5/6] Inserting lab results...")
    labs = []
    for i in range(300):
        labs.append({
            'encounter_id': random.choice(encounter_ids),
            'test_name': random.choice(['CBC', 'BMP', 'Glucose', 'Hemoglobin']),
            'result_value': f'{random.uniform(5, 200):.2f}',
            'created_at': datetime.utcnow()
        })
    db.lab_results.insert_many(labs)
    print("  [OK] Inserted 300 lab results")
    
    print("\n[6/6] Inserting medications...")
    meds = []
    for i in range(200):
        meds.append({
            'encounter_id': random.choice(encounter_ids),
            'medication_name': random.choice(['Aspirin', 'Lisinopril', 'Metformin']),
            'dosage': f'{random.randint(1,4)} tablet(s)',
            'created_at': datetime.utcnow()
        })
    db.medications.insert_many(meds)
    print("  [OK] Inserted 200 medications")
    
    print("\n" + "=" * 80)
    print("MongoDB Setup Complete!")
    print("=" * 80)
    print(f"  Patients   : {db.patients.count_documents({})}")
    print(f"  Encounters : {db.encounters.count_documents({})}")
    print(f"  Lab Results: {db.lab_results.count_documents({})}")
    print(f"  Medications: {db.medications.count_documents({})}")
    print("=" * 80)
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'client' in locals():
        client.close()
