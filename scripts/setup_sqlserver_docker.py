"""Setup SQL Server Database with Sample Data"""
import pyodbc
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()
print("=" * 80)
print("SQL Server Database Setup - Docker")
print("=" * 80)

try:
    # Try to connect
    print("\n[1/8] Connecting to SQL Server...")
    
    # Connection string for Docker SQL Server
    conn_str = (
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=localhost,1433;'
        'UID=sa;'
        'PWD=YourStrong@Passw0rd;'
        'TrustServerCertificate=yes'
    )
    
    try:
        conn = pyodbc.connect(conn_str, timeout=10)
        print("  [OK] Connected to SQL Server")
    except pyodbc.Error as e:
        print(f"  [ERROR] Connection failed: {e}")
        print("\n  Trying alternative connection...")
        conn_str = (
            'DRIVER={SQL Server};'
            'SERVER=localhost,1433;'
            'UID=sa;'
            'PWD=YourStrong@Passw0rd;'
        )
        conn = pyodbc.connect(conn_str, timeout=10)
        print("  [OK] Connected with SQL Server driver")
    
    cursor = conn.cursor()
    
    print("\n[2/8] Creating database...")
    cursor.execute("IF EXISTS (SELECT * FROM sys.databases WHERE name = 'hospital_db_sqlserver') DROP DATABASE hospital_db_sqlserver")
    cursor.execute("CREATE DATABASE hospital_db_sqlserver")
    cursor.execute("USE hospital_db_sqlserver")
    conn.commit()
    print("  [OK] Database created")
    
    print("\n[3/8] Creating tables...")
    cursor.execute("""
        CREATE TABLE patients (
            patient_id INT IDENTITY(1,1) PRIMARY KEY,
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
            encounter_id INT IDENTITY(1,1) PRIMARY KEY,
            patient_id INT NOT NULL,
            encounter_type VARCHAR(50) NOT NULL,
            admission_date DATETIME NOT NULL,
            status VARCHAR(50),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE lab_results (
            lab_id INT IDENTITY(1,1) PRIMARY KEY,
            encounter_id INT NOT NULL,
            test_name VARCHAR(200) NOT NULL,
            result_value VARCHAR(200),
            FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE medications (
            medication_id INT IDENTITY(1,1) PRIMARY KEY,
            encounter_id INT NOT NULL,
            medication_name VARCHAR(200) NOT NULL,
            dosage VARCHAR(100),
            FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE data_change_log (
            change_id BIGINT IDENTITY(1,1) PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            operation VARCHAR(10) NOT NULL,
            record_id INT,
            old_data NVARCHAR(MAX),
            new_data NVARCHAR(MAX),
            changed_at DATETIME DEFAULT GETDATE()
        )
    """)
    conn.commit()
    print("  [OK] Tables created")
    
    print("\n[4/8] Inserting patients...")
    for i in range(50):
        cursor.execute("""
            INSERT INTO patients (medical_record_number, first_name, last_name, 
                                date_of_birth, gender, email)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            f'MRN-SQLSVR-{i+1:05d}',
            fake.first_name(),
            fake.last_name(),
            fake.date_of_birth(minimum_age=18, maximum_age=90),
            random.choice(['male', 'female']),
            fake.email()
        ))
    conn.commit()
    print("  [OK] Inserted 50 patients")
    
    print("\n[5/8] Inserting encounters...")
    for i in range(100):
        cursor.execute("SELECT TOP 1 patient_id FROM patients ORDER BY NEWID()")
        patient_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO encounters (patient_id, encounter_type, admission_date, status)
            VALUES (?, ?, ?, ?)
        """, (
            patient_id,
            random.choice(['Emergency', 'Outpatient', 'Inpatient']),
            fake.date_time_between(start_date='-1y'),
            'finished'
        ))
    conn.commit()
    print("  [OK] Inserted 100 encounters")
    
    print("\n[6/8] Inserting lab results...")
    for i in range(150):
        cursor.execute("SELECT TOP 1 encounter_id FROM encounters ORDER BY NEWID()")
        encounter_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO lab_results (encounter_id, test_name, result_value)
            VALUES (?, ?, ?)
        """, (
            encounter_id,
            random.choice(['CBC', 'BMP', 'Glucose', 'Hemoglobin']),
            f'{random.uniform(5, 200):.2f}'
        ))
    conn.commit()
    print("  [OK] Inserted 150 lab results")
    
    print("\n[7/8] Inserting medications...")
    for i in range(100):
        cursor.execute("SELECT TOP 1 encounter_id FROM encounters ORDER BY NEWID()")
        encounter_id = cursor.fetchone()[0]
        
        cursor.execute("""
            INSERT INTO medications (encounter_id, medication_name, dosage)
            VALUES (?, ?, ?)
        """, (
            encounter_id,
            random.choice(['Aspirin', 'Lisinopril', 'Metformin']),
            f'{random.randint(1,4)} tablet(s)'
        ))
    conn.commit()
    print("  [OK] Inserted 100 medications")
    
    print("\n[8/8] Verifying data...")
    cursor.execute("SELECT COUNT(*) FROM patients")
    patients_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM encounters")
    encounters_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM lab_results")
    labs_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM medications")
    meds_count = cursor.fetchone()[0]
    
    print("\n" + "=" * 80)
    print("SQL Server Setup Complete!")
    print("=" * 80)
    print(f"  Patients   : {patients_count}")
    print(f"  Encounters : {encounters_count}")
    print(f"  Lab Results: {labs_count}")
    print(f"  Medications: {meds_count}")
    print("=" * 80)
    
except pyodbc.Error as e:
    print(f"\n[ERROR] Database error: {e}")
except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
