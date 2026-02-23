"""
Setup MongoDB Database in Docker with Sample Data
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
from faker import Faker

fake = Faker()

print("=" * 80)
print("MongoDB Docker Database Setup")
print("=" * 80)

# Connect to MongoDB in Docker
client = MongoClient('mongodb://localhost:27017/')
db = client['hospital_db_mongodb']

# Drop existing collections
print("\n[1/6] Dropping existing collections...")
db.patients.drop()
db.encounters.drop()
db.lab_results.drop()
db.medications.drop()
db.change_log.drop()
print("  [OK] Collections dropped")

# Create indexes
print("\n[2/6] Creating indexes...")
db.patients.create_index("medical_record_number", unique=True)
db.encounters.create_index("patient_id")
db.lab_results.create_index("patient_id")
db.medications.create_index("patient_id")
db.change_log.create_index("table_name")
print("  [OK] Indexes created")

# Insert patients
print("\n[3/6] Inserting patients...")
patients = []
for i in range(100):
    patient = {
        'medical_record_number': f'MRN-MONGO-{i+1:05d}',
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=90),
        'gender': random.choice(['male', 'female', 'other']),
        'blood_type': random.choice(['A+', 'A-', 'B+', 'B-', 'O+', 'O-']),
        'phone_number': fake.phone_number()[:20],
        'email': fake.email(),
        'address': {
            'city': fake.city(),
            'state': fake.state_abbr()
        },
        'created_at': datetime.utcnow()
    }
    patients.append(patient)

result = db.patients.insert_many(patients)
patient_ids = result.inserted_ids
print(f"  [OK] Inserted {len(patient_ids)} patients")

# Insert encounters
print("\n[4/6] Inserting encounters...")
encounters = []
for i in range(200):
    admission = fake.date_time_between(start_date='-1y', end_date='now')
    encounter = {
        'patient_id': random.choice(patient_ids),
        'encounter_type': random.choice(['Emergency', 'Outpatient', 'Inpatient']),
        'admission_date': admission,
        'discharge_date': admission + timedelta(days=random.randint(1, 5)),
        'chief_complaint': fake.sentence(),
        'diagnosis': fake.sentence(),
        'attending_physician': f'Dr. {fake.last_name()}',
        'status': random.choice(['in-progress', 'finished']),
        'created_at': datetime.utcnow()
    }
    encounters.append(encounter)

result = db.encounters.insert_many(encounters)
encounter_ids = result.inserted_ids
print(f"  [OK] Inserted {len(encounter_ids)} encounters")

# Insert lab results
print("\n[5/6] Inserting lab results...")
lab_results = []
for i in range(300):
    encounter_oid = random.choice(encounter_ids)
    encounter_doc = db.encounters.find_one({'_id': encounter_oid})
    
    lab = {
        'encounter_id': encounter_oid,
        'patient_id': encounter_doc['patient_id'],
        'test_name': random.choice(['CBC', 'BMP', 'Glucose', 'Hemoglobin']),
        'result_value': f'{random.uniform(5, 200):.2f}',
        'result_unit': random.choice(['mg/dL', 'mmol/L', 'g/dL']),
        'performed_date': fake.date_time_between(start_date='-1y', end_date='now'),
        'created_at': datetime.utcnow()
    }
    lab_results.append(lab)

db.lab_results.insert_many(lab_results)
print(f"  [OK] Inserted {len(lab_results)} lab results")

# Insert medications
print("\n[6/6] Inserting medications...")
medications = []
for i in range(200):
    encounter_oid = random.choice(encounter_ids)
    encounter_doc = db.encounters.find_one({'_id': encounter_oid})
    
    med = {
        'encounter_id': encounter_oid,
        'patient_id': encounter_doc['patient_id'],
        'medication_name': random.choice(['Aspirin', 'Lisinopril', 'Metformin']),
        'dosage': f'{random.randint(1, 4)} tablet(s)',
        'frequency': f'{random.randint(1, 3)} times daily',
        'start_date': fake.date_between(start_date='-1y', end_date='now'),
        'status': 'active',
        'created_at': datetime.utcnow()
    }
    medications.append(med)

db.medications.insert_many(medications)
print(f"  [OK] Inserted {len(medications)} medications")

# Summary
print("\n" + "=" * 80)
print("MongoDB Setup Complete")
print("=" * 80)
print(f"  Patients   : {db.patients.count_documents({})}")
print(f"  Encounters : {db.encounters.count_documents({})}")
print(f"  Lab Results: {db.lab_results.count_documents({})}")
print(f"  Medications: {db.medications.count_documents({})}")
print("=" * 80)

client.close()
