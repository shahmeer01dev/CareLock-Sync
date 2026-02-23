"""SQL Server Connection Test and Setup"""
import pyodbc

print("="*80)
print("SQL SERVER - CONNECTION TEST & SETUP")
print("="*80)

# Check available drivers
print("\n[1/3] Checking ODBC drivers...")
drivers = pyodbc.drivers()
print(f"Found {len(drivers)} drivers:")
for d in drivers:
    print(f"  - {d}")

sql_driver = None
for d in ['ODBC Driver 18 for SQL Server', 'ODBC Driver 17 for SQL Server', 'SQL Server']:
    if d in drivers:
        sql_driver = d
        print(f"\n[OK] Using: {sql_driver}")
        break

if not sql_driver:
    print("\n[ERROR] No SQL Server driver found!")
    exit(1)

# Connect
print("\n[2/3] Connecting...")
try:
    conn_str = f'DRIVER={{{sql_driver}}};SERVER=localhost,1433;UID=sa;PWD=YourStrong@Passw0rd;TrustServerCertificate=yes'
    conn = pyodbc.connect(conn_str, timeout=10, autocommit=True)
    print("[OK] Connected!")
    
    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()[0]
    first_line = version.split('\n')[0]
    print(f"[OK] {first_line}")
    
except Exception as e:
    print(f"[ERROR] {e}")
    exit(1)

# Create database
print("\n[3/3] Creating database...")
try:
    cursor.execute("IF EXISTS (SELECT * FROM sys.databases WHERE name = 'hospital_db_sqlserver') DROP DATABASE hospital_db_sqlserver")
    cursor.execute("CREATE DATABASE hospital_db_sqlserver")
    cursor.execute("USE hospital_db_sqlserver")
    print("[OK] Database created")
    
    # Create tables
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
    print("[OK] Tables created")
    
    # Insert data
    cursor.execute("""
        INSERT INTO patients (medical_record_number, first_name, last_name, date_of_birth, gender, email)
        VALUES 
        ('MRN-SQLSVR-00001', 'Alice', 'SQLServer', '1982-03-10', 'female', 'alice.sql@test.com'),
        ('MRN-SQLSVR-00002', 'Bob', 'Database', '1978-07-22', 'male', 'bob.db@test.com')
    """)
    
    cursor.execute("""
        INSERT INTO encounters (patient_id, encounter_type, admission_date, status)
        VALUES (1, 'Emergency', GETDATE(), 'finished'), (2, 'Outpatient', GETDATE(), 'finished')
    """)
    
    cursor.execute("INSERT INTO lab_results (encounter_id, test_name, result_value) VALUES (1, 'CBC', '14.2')")
    cursor.execute("INSERT INTO medications (encounter_id, medication_name, dosage) VALUES (1, 'Metformin', '500mg')")
    print("[OK] Sample data inserted")
    
    cursor.execute("SELECT COUNT(*) FROM patients")
    p = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM encounters")
    e = cursor.fetchone()[0]
    
    print("\n" + "="*80)
    print("SQL SERVER SETUP COMPLETE")
    print("="*80)
    print(f"Patients: {p}, Encounters: {e}")
    print(f"Driver: {sql_driver}")
    print("="*80)
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
