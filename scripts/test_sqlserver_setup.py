"""
SQL Server Connection Test and Setup
"""
import pyodbc
import sys
import os

print("=" * 80)
print("SQL SERVER - CONNECTION TEST & SETUP")
print("=" * 80)

# Test different ODBC drivers
drivers = [
    'ODBC Driver 17 for SQL Server',
    'ODBC Driver 18 for SQL Server',
    'SQL Server Native Client 11.0',
    'SQL Server'
]

print("\n[1/3] Checking available ODBC drivers...")
available_drivers = [d for d in pyodbc.drivers()]
print(f"Found {len(available_drivers)} ODBC drivers:")
for driver in available_drivers:
    print(f"  - {driver}")

# Find SQL Server driver
sql_driver = None
for driver in drivers:
    if driver in available_drivers:
        sql_driver = driver
        print(f"\n[OK] Will use: {sql_driver}")
        break

if not sql_driver:
    print("\n[ERROR] No SQL Server ODBC driver found!")
    print("\nPlease install ODBC Driver 17 or 18:")
    print("  https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server")
    sys.exit(1)

# Test connection
print("\n[2/3] Testing SQL Server connection...")
try:
    conn_str = (
        f'DRIVER={{{sql_driver}}};'
        'SERVER=localhost,1433;'
        'UID=sa;'
        'PWD=YourStrong@Passw0rd;'
        'TrustServerCertificate=yes;'
        'Encrypt=no'
    )
    
    print(f"Connection string: {conn_str[:80]}...")
    
    conn = pyodbc.connect(conn_str, timeout=10)
    print("[OK] Connected to SQL Server!")
    
    cursor = conn.cursor()
    
    # Get version
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()[0]
    print(f"[OK] Version: {version.split('\\n')[0]}")
    
    # List databases
    cursor.execute("SELECT name FROM sys.databases WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb')")
    databases = cursor.fetchall()
    print(f"[OK] User databases: {len(databases)}")
    
    cursor.close()
    conn.close()
    print("[SUCCESS] SQL Server is accessible!")
    
except pyodbc.Error as e:
    print(f"[ERROR] Connection failed: {e}")
    print("\nTrying without TrustServerCertificate...")
    
    try:
        conn_str = (
            f'DRIVER={{{sql_driver}}};'
            'SERVER=localhost,1433;'
            'UID=sa;'
            'PWD=YourStrong@Passw0rd'
        )
        conn = pyodbc.connect(conn_str, timeout=10)
        print("[OK] Connected with basic settings!")
        conn.close()
    except pyodbc.Error as e2:
        print(f"[ERROR] Still failed: {e2}")
        sys.exit(1)

# Create hospital database
print("\n[3/3] Creating hospital database...")
try:
    conn = pyodbc.connect(conn_str, timeout=10, autocommit=True)
    cursor = conn.cursor()
    
    # Drop if exists
    cursor.execute("""
        IF EXISTS (SELECT * FROM sys.databases WHERE name = 'hospital_db_sqlserver')
        BEGIN
            ALTER DATABASE hospital_db_sqlserver SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
            DROP DATABASE hospital_db_sqlserver;
        END
    """)
    print("[OK] Cleaned up old database")
    
    # Create new
    cursor.execute("CREATE DATABASE hospital_db_sqlserver")
    print("[OK] Created hospital_db_sqlserver")
    
    cursor.execute("USE hospital_db_sqlserver")
    
    # Create tables
    print("Creating tables...")
    
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
    print("  [OK] patients")
    
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
    print("  [OK] encounters")
    
    cursor.execute("""
        CREATE TABLE lab_results (
            lab_id INT IDENTITY(1,1) PRIMARY KEY,
            encounter_id INT NOT NULL,
            test_name VARCHAR(200) NOT NULL,
            result_value VARCHAR(200),
            FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
        )
    """)
    print("  [OK] lab_results")
    
    cursor.execute("""
        CREATE TABLE medications (
            medication_id INT IDENTITY(1,1) PRIMARY KEY,
            encounter_id INT NOT NULL,
            medication_name VARCHAR(200) NOT NULL,
            dosage VARCHAR(100),
            FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
        )
    """)
    print("  [OK] medications")
    
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
    print("  [OK] data_change_log")
    
    # Insert sample data
    print("\nInserting sample data...")
    
    cursor.execute("""
        INSERT INTO patients (medical_record_number, first_name, last_name, date_of_birth, gender, email)
        VALUES 
        ('MRN-SQLSVR-00001', 'Alice', 'SQLServer', '1982-03-10', 'female', 'alice.sql@test.com'),
        ('MRN-SQLSVR-00002', 'Bob', 'Database', '1978-07-22', 'male', 'bob.db@test.com')
    """)
    print("  [OK] 2 patients")
    
    cursor.execute("""
        INSERT INTO encounters (patient_id, encounter_type, admission_date, status)
        VALUES 
        (1, 'Emergency', GETDATE(), 'finished'),
        (2, 'Outpatient', GETDATE(), 'finished')
    """)
    print("  [OK] 2 encounters")
    
    cursor.execute("""
        INSERT INTO lab_results (encounter_id, test_name, result_value)
        VALUES (1, 'CBC', '14.2')
    """)
    print("  [OK] 1 lab result")
    
    cursor.execute("""
        INSERT INTO medications (encounter_id, medication_name, dosage)
        VALUES (1, 'Metformin', '500mg')
    """)
    print("  [OK] 1 medication")
    
    # Verify
    cursor.execute("SELECT COUNT(*) FROM patients")
    patients = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM encounters")
    encounters = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM lab_results")
    labs = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM medications")
    meds = cursor.fetchone()[0]
    
    print("\n" + "=" * 80)
    print("SQL SERVER SETUP COMPLETE")
    print("=" * 80)
    print(f"  Patients   : {patients}")
    print(f"  Encounters : {encounters}")
    print(f"  Lab Results: {labs}")
    print(f"  Medications: {meds}")
    print("=" * 80)
    print(f"\nODBC Driver: {sql_driver}")
    print("Database   : hospital_db_sqlserver")
    print("Status     : OPERATIONAL")
    print("=" * 80)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
