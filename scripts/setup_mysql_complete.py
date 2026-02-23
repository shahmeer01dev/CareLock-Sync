"""
Complete MySQL Hospital Database Setup with Sample Data
Includes: Schema creation, data generation, CDC triggers
"""
import pymysql
import random
from datetime import datetime, timedelta
from faker import Faker
import sys

fake = Faker()

print("=" * 80)
print("MySQL Hospital Database - Complete Setup")
print("=" * 80)

# Configuration
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',  # Change if needed
    'charset': 'utf8mb4'
}

try:
    # Connect to MySQL server
    conn = pymysql.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()
    
    # Step 1: Create Database
    print("\n[1/7] Creating database...")
    cursor.execute("DROP DATABASE IF EXISTS hospital_db_mysql")
    cursor.execute("CREATE DATABASE hospital_db_mysql CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute("USE hospital_db_mysql")
    print("  [OK] Database created: hospital_db_mysql")
    
    # Step 2: Create Tables
    print("\n[2/7] Creating tables...")
    
    # Patients table
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
            address_line1 VARCHAR(200),
            city VARCHAR(100),
            state VARCHAR(50),
            zip_code VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_last_name (last_name),
            INDEX idx_mrn (medical_record_number)
        ) ENGINE=InnoDB
    """)
    
    # Encounters table
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
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
            INDEX idx_patient (patient_id),
            INDEX idx_admission (admission_date)
        ) ENGINE=InnoDB
    """)
    
    # Lab Results table
    cursor.execute("""
        CREATE TABLE lab_results (
            lab_id INT AUTO_INCREMENT PRIMARY KEY,
            encounter_id INT NOT NULL,
            patient_id INT NOT NULL,
            test_name VARCHAR(200) NOT NULL,
            test_code VARCHAR(50),
            result_value VARCHAR(200),
            result_unit VARCHAR(50),
            performed_date DATETIME NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        ) ENGINE=InnoDB
    """)
    
    # Medications table
    cursor.execute("""
        CREATE TABLE medications (
            medication_id INT AUTO_INCREMENT PRIMARY KEY,
            encounter_id INT NOT NULL,
            patient_id INT NOT NULL,
            medication_name VARCHAR(200) NOT NULL,
            dosage VARCHAR(100),
            frequency VARCHAR(100),
            route VARCHAR(50),
            start_date DATE NOT NULL,
            status VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        ) ENGINE=InnoDB
    """)
    
    # CDC Change Log table
    cursor.execute("""
        CREATE TABLE data_change_log (
            change_id BIGINT AUTO_INCREMENT PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            operation VARCHAR(10) NOT NULL,
            record_id INT,
            old_data JSON,
            new_data JSON,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_name VARCHAR(100),
            INDEX idx_table (table_name),
            INDEX idx_time (changed_at)
        ) ENGINE=InnoDB
    """)
    
    conn.commit()
    print("  [OK] Tables created: patients, encounters, lab_results, medications, data_change_log")
    
    # Step 3: Insert Sample Data
    print("\n[3/7] Inserting sample patients...")
    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    genders = ['male', 'female', 'other']
    
    patient_ids = []
    for i in range(100):
        cursor.execute("""
            INSERT INTO patients (medical_record_number, first_name, last_name, 
                                 date_of_birth, gender, blood_type, phone_number, 
                                 email, address_line1, city, state, zip_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
    
    # Step 4: Insert Encounters
    print("\n[4/7] Inserting sample encounters...")
    encounter_types = ['Emergency', 'Outpatient', 'Inpatient', 'Observation']
    statuses = ['in-progress', 'finished', 'planned']
    
    encounter_ids = []
    for i in range(200):
        patient_id = random.choice(patient_ids)
        admission = fake.date_time_between(start_date='-1y', end_date='now')
        
        cursor.execute("""
            INSERT INTO encounters (patient_id, encounter_type, admission_date,
                                   discharge_date, chief_complaint, diagnosis,
                                   attending_physician, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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
    
    # Step 5: Insert Lab Results
    print("\n[5/7] Inserting sample lab results...")
    tests = [
        ('CBC', 'Complete Blood Count'),
        ('BMP', 'Basic Metabolic Panel'),
        ('Glucose', 'Blood Glucose'),
        ('Hemoglobin', 'Hemoglobin Level')
    ]
    
    for i in range(500):
        encounter_id = random.choice(encounter_ids)
        cursor.execute("SELECT patient_id FROM encounters WHERE encounter_id = %s", (encounter_id,))
        patient_id = cursor.fetchone()[0]
        
        test = random.choice(tests)
        cursor.execute("""
            INSERT INTO lab_results (encounter_id, patient_id, test_name, test_code,
                                    result_value, result_unit, performed_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            encounter_id,
            patient_id,
            test[1],
            test[0],
            f'{random.uniform(5, 200):.2f}',
            'mg/dL',
            fake.date_time_between(start_date='-1y', end_date='now')
        ))
    
    conn.commit()
    print(f"  [OK] Inserted 500 lab results")
    
    # Step 6: Insert Medications
    print("\n[6/7] Inserting sample medications...")
    medications = [
        'Aspirin 81mg', 'Lisinopril 10mg', 'Metformin 500mg',
        'Atorvastatin 20mg', 'Levothyroxine 50mcg'
    ]
    routes = ['oral', 'IV', 'IM']
    
    for i in range(300):
        encounter_id = random.choice(encounter_ids)
        cursor.execute("SELECT patient_id FROM encounters WHERE encounter_id = %s", (encounter_id,))
        patient_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO medications (encounter_id, patient_id, medication_name,
                                    dosage, frequency, route, start_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            encounter_id,
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
    
    # Step 7: Create CDC Triggers
    print("\n[7/7] Creating CDC triggers...")
    
    tables = ['patients', 'encounters', 'lab_results', 'medications']
    for table in tables:
        # Get primary key
        cursor.execute(f"""
            SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = 'hospital_db_mysql'
            AND TABLE_NAME = '{table}'
            AND CONSTRAINT_NAME = 'PRIMARY'
            LIMIT 1
        """)
        pk = cursor.fetchone()
        pk_col = pk[0] if pk else f'{table[:-1]}_id'
        
        # Drop existing triggers
        for op in ['insert', 'update', 'delete']:
            try:
                cursor.execute(f"DROP TRIGGER IF EXISTS {table}_after_{op}")
            except:
                pass
        
        # INSERT trigger
        cursor.execute(f"""
            CREATE TRIGGER {table}_after_insert
            AFTER INSERT ON {table}
            FOR EACH ROW
            INSERT INTO data_change_log (table_name, operation, record_id, new_data, user_name)
            VALUES ('{table}', 'INSERT', NEW.{pk_col}, 
                    JSON_OBJECT('{pk_col}', NEW.{pk_col}), USER())
        """)
        
        # UPDATE trigger
        cursor.execute(f"""
            CREATE TRIGGER {table}_after_update
            AFTER UPDATE ON {table}
            FOR EACH ROW
            INSERT INTO data_change_log (table_name, operation, record_id, old_data, new_data, user_name)
            VALUES ('{table}', 'UPDATE', NEW.{pk_col},
                    JSON_OBJECT('{pk_col}', OLD.{pk_col}),
                    JSON_OBJECT('{pk_col}', NEW.{pk_col}), USER())
        """)
        
        # DELETE trigger
        cursor.execute(f"""
            CREATE TRIGGER {table}_after_delete
            AFTER DELETE ON {table}
            FOR EACH ROW
            INSERT INTO data_change_log (table_name, operation, record_id, old_data, user_name)
            VALUES ('{table}', 'DELETE', OLD.{pk_col},
                    JSON_OBJECT('{pk_col}', OLD.{pk_col}), USER())
        """)
        
        print(f"  [OK] CDC triggers created for: {table}")
    
    conn.commit()
    
    # Final Summary
    print("\n" + "=" * 80)
    print("MySQL Database Setup COMPLETE")
    print("=" * 80)
    cursor.execute("SELECT COUNT(*) FROM patients")
    print(f"  Patients      : {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM encounters")
    print(f"  Encounters    : {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM lab_results")
    print(f"  Lab Results   : {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM medications")
    print(f"  Medications   : {cursor.fetchone()[0]}")
    cursor.execute("SELECT COUNT(*) FROM data_change_log")
    print(f"  Change Log    : {cursor.fetchone()[0]} entries")
    print("\nConnection: mysql://root:root@localhost:3306/hospital_db_mysql")
    print("=" * 80)
    
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    if 'conn' in locals():
        conn.close()
