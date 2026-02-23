"""
Setup MongoDB Hospital Database with Sample Data
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
from faker import Faker
from bson import ObjectId

fake = Faker()

print("=" * 80)
print("MongoDB Hospital Database Setup")
print("=" * 80)

# Connect to MongoDB
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

# Create collections with indexes
print("\n[2/6] Creating collections and indexes...")

# Patients collection
db.patients.create_index("medical_record_number", unique=True)
db.patients.create_index("last_name")

# Encounters collection
db.encounters.create_index("patient_id")
db.encounters.create_index("admission_date")

# Lab results collection
db.lab_results.create_index("encounter_id")
db.lab_results.create_index("patient_id")

# Medications collection
db.medications.create_index("encounter_id")
db.medications.create_index("patient_id")

# Change log collection
db.change_log.create_index("table_name")
db.change_log.create_index("changed_at")

print("  [OK] Indexes created")

# Insert sample patients
print("\n[3/6] Inserting sample patients...")
blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
genders = ['male', 'female', 'other']

patients = []
for i in range(100):
    patient = {
        'medical_record_number': f'MRN-MONGO-{i+1:05d}',
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=90),
        'gender': random.choice(genders),
        'blood_type': random.choice(blood_types),
        'phone_number': fake.phone_number()[:20],
        'email': fake.email(),
        'address': {
            'line1': fake.street_address(),
            'line2': None,
            'city': fake.city(),
            'state': fake.state_abbr(),
            'zip_code': fake.zipcode()
        },
        'emergency_contact': {
            'name': fake.name(),
            'phone': fake.phone_number()[:20]
        },
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    patients.append(patient)

result = db.patients.insert_many(patients)
patient_ids = result.inserted_ids
print(f"  [OK] Inserted {len(patient_ids)} patients")

# Insert encounters
print("\n[4/6] Inserting sample encounters...")
encounter_types = ['Emergency', 'Outpatient', 'Inpatient', 'Observation']
statuses = ['in-progress', 'finished', 'planned']

encounters = []
for i in range(200):
    patient_id = random.choice(patient_ids)
    admission = fake.date_time_between(start_date='-1y', end_date='now')
    
    encounter = {
        'patient_id': patient_id,
        'encounter_type': random.choice(encounter_types),
        'admission_date': admission,
        'discharge_date': admission + timedelta(days=random.randint(1, 7)),
        'chief_complaint': fake.sentence(),
        'diagnosis': fake.sentence(),
        'attending_physician': f'Dr. {fake.last_name()}',
        'department': random.choice(['Cardiology', 'Neurology', 'Emergency', 'Surgery']),
        'room_number': f'{random.randint(100, 999)}',
        'status': random.choice(statuses),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    encounters.append(encounter)

result = db.encounters.insert_many(encounters)
encounter_ids = result.inserted_ids
print(f"  [OK] Inserted {len(encounter_ids)} encounters")

# Insert lab results
print("\n[5/6] Inserting sample lab results...")
tests = [
    ('CBC', 'Complete Blood Count', 'cells/uL'),
    ('BMP', 'Basic Metabolic Panel', 'mmol/L'),
    ('Glucose', 'Blood Glucose', 'mg/dL'),
    ('Hemoglobin', 'Hemoglobin Level', 'g/dL')
]

lab_results = []
for i in range(500):
    encounter_oid = random.choice(encounter_ids)
    encounter_doc = db.encounters.find_one({'_id': encounter_oid})
    patient_id = encounter_doc['patient_id']
    
    test = random.choice(tests)
    lab = {
        'encounter_id': encounter_oid,
        'patient_id': patient_id,
        'test_name': test[1],
        'test_code': test[0],
        'result_value': f'{random.uniform(5, 200):.2f}',
        'result_unit': test[2],
        'reference_range': '0-100',
        'abnormal_flag': random.choice(['normal', 'high', 'low']),
        'performed_date': fake.date_time_between(start_date='-1y', end_date='now'),
        'result_date': datetime.utcnow(),
        'performing_lab': 'Central Lab',
        'technician_name': fake.name(),
        'created_at': datetime.utcnow()
    }
    lab_results.append(lab)

db.lab_results.insert_many(lab_results)
print(f"  [OK] Inserted {len(lab_results)} lab results")

# Insert medications
print("\n[6/6] Inserting sample medications...")
medications_list = [
    'Aspirin 81mg', 'Lisinopril 10mg', 'Metformin 500mg',
    'Atorvastatin 20mg', 'Levothyroxine 50mcg'
]
routes = ['oral', 'IV', 'IM', 'topical']

medications = []
for i in range(300):
    encounter_oid = random.choice(encounter_ids)
    encounter_doc = db.encounters.find_one({'_id': encounter_oid})
    patient_id = encounter_doc['patient_id']
    
    med = {
        'encounter_id': encounter_oid,
        'patient_id': patient_id,
        'medication_name': random.choice(medications_list),
        'dosage': f'{random.randint(1, 4)} tablet(s)',
        'frequency': f'{random.randint(1, 3)} times daily',
        'route': random.choice(routes),
        'start_date': fake.date_between(start_date='-1y', end_date='now'),
        'end_date': None,
        'prescribing_physician': f'Dr. {fake.last_name()}',
        'pharmacy_notes': fake.sentence(),
        'status': 'active',
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    medications.append(med)

db.medications.insert_many(medications)
print(f"  [OK] Inserted {len(medications)} medications")

# Summary
print("\n" + "=" * 80)
print("MongoDB Database Setup Complete")
print("=" * 80)
print(f"  Patients   : {db.patients.count_documents({})}")
print(f"  Encounters : {db.encounters.count_documents({})}")
print(f"  Lab Results: {db.lab_results.count_documents({})}")
print(f"  Medications: {db.medications.count_documents({})}")
print("=" * 80)

client.close()
