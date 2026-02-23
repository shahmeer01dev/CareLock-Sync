"""
Setup MySQL Database in Docker with Sample Data
"""
import pymysql
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

print("=" * 80)
print("MySQL Docker Database Setup")
print("=" * 80)

# Connect to MySQL in Docker
conn = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    password='root',
    charset='utf8mb4',
    cursorclass=pymysql.cursors.DictCursor
)

cursor = conn.cursor()

try:
    # Create database
    print("\n[1/6] Creating database...")
    cursor.execute("DROP DATABASE IF EXISTS hospital_db_mysql")
    cursor.execute("CREATE DATABASE hospital_db_mysql")
    cursor.execute("USE hospital_db_mysql")
    print("  [OK] Database created")
    
    # Create tables
    print("\n[2/6] Creating tables...")
    
    cursor.execute("""
        CREATE TABLE patients (
            patient_id INT AUTO_INCREMENT PRIMARY KEY,
            medical_record_number VARCHAR(50) UNIQUE NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            date_of_birth DATE NOT NULL,
            gender VARCHAR(20),
            blood_type VARCHAR(10),
            phone_number VARCHAR(20),
            email VARCHAR(100),
            city VARCHAR(100),
            state VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE encounters (
            encounter_id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            encounter_type VARCHAR(50) NOT NULL,
            admission_date DATETIME NOT NULL,
            discharge_date DATETIME,
            chief_complaint TEXT,
            diagnosis TEXT,
            attending_physician VARCHAR(200),
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE lab_results (
            lab_id INT AUTO_INCREMENT PRIMARY KEY,
            encounter_id INT NOT NULL,
            patient_id INT NOT NULL,
            test_name VARCHAR(200) NOT NULL,
            result_value VARCHAR(200),
            result_unit VARCHAR(50),
            performed_date DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE medications (
            medication_id INT AUTO_INCREMENT PRIMARY KEY,
            encounter_id INT NOT NULL,
            patient_id INT NOT NULL,
            medication_name VARCHAR(200) NOT NULL,
            dosage VARCHAR(100),
            frequency VARCHAR(100),
            start_date DATE NOT NULL,
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE data_change_log (
            change_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            operation VARCHAR(10) NOT NULL,
            record_id INT,
            old_data JSON,
            new_data JSON,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_table (table_name),
            INDEX idx_time (changed_at)
        )
    """)
    
    print("  [OK] Tables created")
    
    # Insert patients
    print("\n[3/6] Inserting patients...")
    patient_ids = []
    for i in range(100):
        cursor.execute("""
            INSERT INTO patients (
                medical_record_number, first_name, last_name, date_of_birth,
                gender, blood_type, phone_number, email, city, state
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            f'MRN-MYSQL-{i+1:05d}',
            fake.first_name(),
            fake.last_name(),
            fake.date_of_birth(minimum_age=18, maximum_age=90),
            random.choice(['male', 'female', 'other']),
            random.choice(['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']),
            fake.phone_number()[:20],
            fake.email(),
            fake.city(),
            fake.state_abbr()
        ))
        patient_ids.append(cursor.lastrowid)
    
    conn.commit()
    print(f"  [OK] Inserted {len(patient_ids)} patients")
    
    # Insert encounters
    print("\n[4/6] Inserting encounters...")
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
            random.choice(['Emergency', 'Outpatient', 'Inpatient']),
            admission,
            admission + timedelta(days=random.randint(1, 5)),
            fake.sentence(),
            fake.sentence(),
            f'Dr. {fake.last_name()}',
            random.choice(['in-progress', 'finished'])
        ))
        encounter_ids.append(cursor.lastrowid)
    
    conn.commit()
    print(f"  [OK] Inserted {len(encounter_ids)} encounters")
    
    # Insert lab results
    print("\n[5/6] Inserting lab results...")
    for i in range(300):
        encounter_id = random.choice(encounter_ids)
        cursor.execute("SELECT patient_id FROM encounters WHERE encounter_id = %s", (encounter_id,))
        patient_id = cursor.fetchone()['patient_id']
        
        cursor.execute("""
            INSERT INTO lab_results (
                encounter_id, patient_id, test_name, result_value,
                result_unit, performed_date
            ) VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            encounter_id,
            patient_id,
            random.choice(['CBC', 'BMP', 'Glucose', 'Hemoglobin']),
            f'{random.uniform(5, 200):.2f}',
            random.choice(['mg/dL', 'mmol/L', 'g/dL']),
            fake.date_time_between(start_date='-1y', end_date='now')
        ))
    
    conn.commit()
    print(f"  [OK] Inserted 300 lab results")
    
    # Insert medications
    print("\n[6/6] Inserting medications...")
    for i in range(200):
        encounter_id = random.choice(encounter_ids)
        cursor.execute("SELECT patient_id FROM encounters WHERE encounter_id = %s", (encounter_id,))
        patient_id = cursor.fetchone()['patient_id']
        
        cursor.execute("""
            INSERT INTO medications (
                encounter_id, patient_id, medication_name, dosage,
                frequency, start_date, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            encounter_id,
            patient_id,
            random.choice(['Aspirin', 'Lisinopril', 'Metformin', 'Atorvastatin']),
            f'{random.randint(1, 4)} tablet(s)',
            f'{random.randint(1, 3)} times daily',
            fake.date_between(start_date='-1y', end_date='now'),
            'active'
        ))
    
    conn.commit()
    print(f"  [OK] Inserted 200 medications")
    
    # Summary
    print("\n" + "=" * 80)
    print("MySQL Setup Complete")
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
    cursor.close()
    conn.close()
