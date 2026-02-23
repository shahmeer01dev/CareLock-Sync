"""
Complete MongoDB Hospital Database Setup with Sample Data
Includes: Collections, indexes, sample data, change tracking
"""
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
from faker import Faker
from bson import ObjectId
import sys

fake = Faker()

print("=" * 80)
print("MongoDB Hospital Database - Complete Setup")
print("=" * 80)

try:
    # Connect to MongoDB
    print("\n[1/6] Connecting to MongoDB...")
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=5000)
    # Test connection
    client.admin.command('ping')
    print("  [OK] Connected to MongoDB")
    
    db = client['hospital_db_mongodb']
    
    # Drop existing collections
    print("\n[2/6] Dropping existing collections...")
    db.patients.drop()
    db.encounters.drop()
    db.lab_results.drop()
    db.medications.drop()
    db.change_log.drop()
    print("  [OK] Collections dropped")
    
    # Create indexes
    print("\n[3/6] Creating indexes...")
    db.patients.create_index("medical_record_number", unique=True)
    db.patients.create_index("last_name")
    db.encounters.create_index("patient_id")
    db.encounters.create_index("admission_date")
    db.lab_results.create_index("encounter_id")
    db.lab_results.create_index("patient_id")
    db.medications.create_index("encounter_id")
    db.medications.create_index("patient_id")
    db.change_log.create_index("table_name")
    db.change_log.create_index("changed_at")
    print("  [OK] Indexes created")
    
    # Insert patients
    print("\n[4/6] Inserting sample patients...")
    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    genders = ['male', 'female', 'other']
    
    patients = []
    for i in range(100):
        # Convert date to datetime for MongoDB compatibility
        dob = fake.date_of_birth(minimum_age=18, maximum_age=90)
        dob_datetime = datetime.combine(dob, datetime.min.time())
        
        patient = {
            'medical_record_number': f'MRN-MONGO-{i+1:05d}',
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'date_of_birth': dob_datetime,  # Use datetime instead of date
            'gender': random.choice(genders),
            'blood_type': random.choice(blood_types),
            'phone_number': fake.phone_number()[:20],
            'email': fake.email(),
            'address': {
                'line1': fake.street_address(),
                'city': fake.city(),
                'state': fake.state_abbr(),
                'zip_code': fake.zipcode()
            },
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        patients.append(patient)
    
    result = db.patients.insert_many(patients)
    patient_ids = result.inserted_ids
    print(f"  [OK] Inserted {len(patient_ids)} patients")
    
    # Insert encounters
    print("\n[5/6] Inserting sample encounters...")
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
            'status': random.choice(statuses),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        encounters.append(encounter)
    
    result = db.encounters.insert_many(encounters)
    encounter_ids = result.inserted_ids
    print(f"  [OK] Inserted {len(encounter_ids)} encounters")
    
    # Insert lab results
    print("\n[6/6] Inserting sample lab results and medications...")
    tests = [
        ('CBC', 'Complete Blood Count'),
        ('BMP', 'Basic Metabolic Panel'),
        ('Glucose', 'Blood Glucose'),
        ('Hemoglobin', 'Hemoglobin Level')
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
            'result_unit': 'mg/dL',
            'performed_date': fake.date_time_between(start_date='-1y', end_date='now'),
            'created_at': datetime.utcnow()
        }
        lab_results.append(lab)
    
    db.lab_results.insert_many(lab_results)
    print(f"  [OK] Inserted {len(lab_results)} lab results")
    
    # Insert medications
    medications_list = [
        'Aspirin 81mg', 'Lisinopril 10mg', 'Metformin 500mg',
        'Atorvastatin 20mg', 'Levothyroxine 50mcg'
    ]
    routes = ['oral', 'IV', 'IM']
    
    medications = []
    for i in range(300):
        encounter_oid = random.choice(encounter_ids)
        encounter_doc = db.encounters.find_one({'_id': encounter_oid})
        patient_id = encounter_doc['patient_id']
        
        # Convert date to datetime for MongoDB
        start_date = fake.date_between(start_date='-1y', end_date='now')
        start_datetime = datetime.combine(start_date, datetime.min.time())
        
        med = {
            'encounter_id': encounter_oid,
            'patient_id': patient_id,
            'medication_name': random.choice(medications_list),
            'dosage': f'{random.randint(1, 4)} tablet(s)',
            'frequency': f'{random.randint(1, 3)} times daily',
            'route': random.choice(routes),
            'start_date': start_datetime,  # Use datetime instead of date
            'status': 'active',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        medications.append(med)
    
    db.medications.insert_many(medications)
    print(f"  [OK] Inserted {len(medications)} medications")
    
    # Summary
    print("\n" + "=" * 80)
    print("MongoDB Database Setup COMPLETE")
    print("=" * 80)
    print(f"  Patients      : {db.patients.count_documents({})}")
    print(f"  Encounters    : {db.encounters.count_documents({})}")
    print(f"  Lab Results   : {db.lab_results.count_documents({})}")
    print(f"  Medications   : {db.medications.count_documents({})}")
    print(f"  Change Log    : {db.change_log.count_documents({})} entries")
    print("\nConnection: mongodb://localhost:27017/hospital_db_mongodb")
    print("=" * 80)
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'client' in locals():
        client.close()
