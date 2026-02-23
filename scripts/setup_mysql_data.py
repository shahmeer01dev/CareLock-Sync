"""
Setup MySQL Hospital Database with Sample Data
"""
import pymysql
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# MySQL connection
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='root',  # Change this to your MySQL root password
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

print("=" * 80)
print("MySQL Hospital Database Setup")
print("=" * 80)

try:
    cursor = conn.cursor()
    
    # Create database
    print("\n[1/6] Creating database...")
    cursor.execute("DROP DATABASE IF EXISTS hospital_db_mysql")
    cursor.execute("""
        CREATE DATABASE hospital_db_mysql 
        CHARACTER SET utf8mb4 
        COLLATE utf8mb4_unicode_ci
    """)
    cursor.execute("USE hospital_db_mysql")
    print("  [OK] Database created")
    
    # Read and execute schema
    print("\n[2/6] Creating tables...")
    with open(r'C:\Projects\CareLock-Sync\scripts\setup_mysql_db.sql', 'r') as f:
        sql_script = f.read()
    
    # Split by semicolon and execute each statement
    statements = [s.strip() for s in sql_script.split(';') if s.strip()]
    for statement in statements:
        if statement.upper().startswith(('CREATE TABLE', 'CREATE INDEX')):
            cursor.execute(statement)
    
    conn.commit()
    print("  [OK] Tables created")
    
    # Insert sample patients
    print("\n[3/6] Inserting sample patients...")
    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    genders = ['male', 'female', 'other']
    
    patient_ids = []
    for i in range(100):
        cursor.execute("""
            INSERT INTO patients (
                medical_record_number, first_name, last_name, date_of_birth,
                gender, blood_type, phone_number, email, address_line1,
                city, state, zip_code
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            f'MRN-MYSQL-{i+1:05d}',
            fake.first_name(),
            fake.last_name(),
            fake.date_of_birth(minimum_age=18, maximum_age=90),
            random.choice(genders),
            random.choice(blood_types),
            fake.phone_number()[:20],
            fake.email(),
            fake.street_address(),
            fake.city(),
            fake.state_abbr(),
            fake.zipcode()
        ))
        patient_ids.append(cursor.lastrowid)
    
    conn.commit()
    print(f"  [OK] Inserted {len(patient_ids)} patients")
    
    # Insert encounters
    print("\n[4/6] Inserting sample encounters...")
    encounter_types = ['Emergency', 'Outpatient', 'Inpatient', 'Observation']
    statuses = ['in-progress', 'finished', 'planned']
    
    encounter_ids = []
    for i in range(200):
        patient_id = random.choice(patient_ids)
        admission = fake.date_time_between(start_date='-1y', end_date='now')
        
        cursor.execute("""
            INSERT INTO encounters (
                patient_id, encounter_type, admission_date, discharge_date,
                chief_complaint, diagnosis, attending_physician, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            patient_id,
            random.choice(encounter_types),
            admission,
            admission + timedelta(days=random.randint(1, 7)),
            fake.sentence(),
            fake.sentence(),
            f'Dr. {fake.last_name()}',
            random.choice(statuses)
        ))
        encounter_ids.append(cursor.lastrowid)
    
    conn.commit()
    print(f"  [OK] Inserted {len(encounter_ids)} encounters")
    
    # Insert lab results
    print("\n[5/6] Inserting sample lab results...")
    tests = [
        ('CBC', 'Complete Blood Count', 'cells/uL'),
        ('BMP', 'Basic Metabolic Panel', 'mmol/L'),
        ('Glucose', 'Blood Glucose', 'mg/dL'),
        ('Hemoglobin', 'Hemoglobin Level', 'g/dL')
    ]
    
    for i in range(500):
        encounter = random.choice(encounter_ids)
        cursor.execute("SELECT patient_id FROM encounters WHERE encounter_id = %s", (encounter,))
        patient_id = cursor.fetchone()['patient_id']
        
        test = random.choice(tests)
        cursor.execute("""
            INSERT INTO lab_results (
                encounter_id, patient_id, test_name, test_code,
                result_value, result_unit, performed_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            encounter,
            patient_id,
            test[1],
            test[0],
            f'{random.uniform(5, 200):.2f}',
            test[2],
            fake.date_time_between(start_date='-1y', end_date='now')
        ))
    
    conn.commit()
    print(f"  [OK] Inserted 500 lab results")
    
    # Insert medications
    print("\n[6/6] Inserting sample medications...")
    medications = [
        'Aspirin 81mg', 'Lisinopril 10mg', 'Metformin 500mg',
        'Atorvastatin 20mg', 'Levothyroxine 50mcg'
    ]
    routes = ['oral', 'IV', 'IM', 'topical']
    
    for i in range(300):
        encounter = random.choice(encounter_ids)
        cursor.execute("SELECT patient_id FROM encounters WHERE encounter_id = %s", (encounter,))
        patient_id = cursor.fetchone()['patient_id']
        
        cursor.execute("""
            INSERT INTO medications (
                encounter_id, patient_id, medication_name,
                dosage, frequency, route, start_date, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            encounter,
            patient_id,
            random.choice(medications),
            f'{random.randint(1, 4)} tablet(s)',
            f'{random.randint(1, 3)} times daily',
            random.choice(routes),
            fake.date_between(start_date='-1y', end_date='now'),
            'active'
        ))
    
    conn.commit()
    print(f"  [OK] Inserted 300 medications")
    
    # Summary
    print("\n" + "=" * 80)
    print("MySQL Database Setup Complete")
    print("=" * 80)
    cursor.execute("SELECT COUNT(*) as cnt FROM patients")
    print(f"  Patients   : {cursor.fetchone()['cnt']}")
    cursor.execute("SELECT COUNT(*) as cnt FROM encounters")
    print(f"  Encounters : {cursor.fetchone()['cnt']}")
    cursor.execute("SELECT COUNT(*) as cnt FROM lab_results")
    print(f"  Lab Results: {cursor.fetchone()['cnt']}")
    cursor.execute("SELECT COUNT(*) as cnt FROM medications")
    print(f"  Medications: {cursor.fetchone()['cnt']}")
    print("=" * 80)
    
finally:
    conn.close()
