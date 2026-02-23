"""Setup MySQL Database with Sample Data"""
import pymysql
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()
print("=" * 80)
print("MySQL Database Setup - Docker")
print("=" * 80)

try:
    conn = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='root',
        charset='utf8mb4'
    )
    cursor = conn.cursor()
    
    print("\n[1/7] Creating database...")
    cursor.execute("DROP DATABASE IF EXISTS hospital_db_mysql")
    cursor.execute("CREATE DATABASE hospital_db_mysql")
    cursor.execute("USE hospital_db_mysql")
    print("  [OK] Database created")
    
    print("\n[2/7] Creating tables...")
    cursor.execute("""
        CREATE TABLE patients (
            patient_id INT AUTO_INCREMENT PRIMARY KEY,
            medical_record_number VARCHAR(50) UNIQUE NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            date_of_birth DATE NOT NULL,
            gender VARCHAR(20),
            email VARCHAR(100)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE encounters (
            encounter_id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            encounter_type VARCHAR(50) NOT NULL,
            admission_date DATETIME NOT NULL,
            status VARCHAR(50),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE lab_results (
            lab_id INT AUTO_INCREMENT PRIMARY KEY,
            encounter_id INT NOT NULL,
            test_name VARCHAR(200) NOT NULL,
            result_value VARCHAR(200),
            FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE medications (
            medication_id INT AUTO_INCREMENT PRIMARY KEY,
            encounter_id INT NOT NULL,
            medication_name VARCHAR(200) NOT NULL,
            dosage VARCHAR(100),
            FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
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
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("  [OK] Tables created")
    
    print("\n[3/7] Inserting patients...")
    patient_ids = []
    for i in range(100):
        cursor.execute("""
            INSERT INTO patients (medical_record_number, first_name, last_name, 
                                date_of_birth, gender, email)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            f'MRN-MYSQL-{i+1:05d}',
            fake.first_name(),
            fake.last_name(),
            fake.date_of_birth(minimum_age=18, maximum_age=90),
            random.choice(['male', 'female']),
            fake.email()
        ))
        patient_ids.append(cursor.lastrowid)
    conn.commit()
    print(f"  [OK] Inserted {len(patient_ids)} patients")
    
    print("\n[4/7] Inserting encounters...")
    encounter_ids = []
    for i in range(200):
        cursor.execute("""
            INSERT INTO encounters (patient_id, encounter_type, admission_date, status)
            VALUES (%s, %s, %s, %s)
        """, (
            random.choice(patient_ids),
            random.choice(['Emergency', 'Outpatient', 'Inpatient']),
            fake.date_time_between(start_date='-1y'),
            'finished'
        ))
        encounter_ids.append(cursor.lastrowid)
    conn.commit()
    print(f"  [OK] Inserted {len(encounter_ids)} encounters")
    
    print("\n[5/7] Inserting lab results...")
    for i in range(300):
        cursor.execute("""
            INSERT INTO lab_results (encounter_id, test_name, result_value)
            VALUES (%s, %s, %s)
        """, (
            random.choice(encounter_ids),
            random.choice(['CBC', 'BMP', 'Glucose', 'Hemoglobin']),
            f'{random.uniform(5, 200):.2f}'
        ))
    conn.commit()
    print("  [OK] Inserted 300 lab results")
    
    print("\n[6/7] Inserting medications...")
    for i in range(200):
        cursor.execute("""
            INSERT INTO medications (encounter_id, medication_name, dosage)
            VALUES (%s, %s, %s)
        """, (
            random.choice(encounter_ids),
            random.choice(['Aspirin', 'Lisinopril', 'Metformin']),
            f'{random.randint(1,4)} tablet(s)'
        ))
    conn.commit()
    print("  [OK] Inserted 200 medications")
    
    print("\n[7/7] Verifying data...")
    cursor.execute("SELECT COUNT(*) as cnt FROM patients")
    patients_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM encounters")
    encounters_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM lab_results")
    labs_count = cursor.fetchone()['cnt']
    cursor.execute("SELECT COUNT(*) as cnt FROM medications")
    meds_count = cursor.fetchone()['cnt']
    
    print("\n" + "=" * 80)
    print("MySQL Setup Complete!")
    print("=" * 80)
    print(f"  Patients   : {patients_count}")
    print(f"  Encounters : {encounters_count}")
    print(f"  Lab Results: {labs_count}")
    print(f"  Medications: {meds_count}")
    print("=" * 80)
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
