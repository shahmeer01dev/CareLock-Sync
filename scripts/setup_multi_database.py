"""
Multi-Database Setup Script
Creates MySQL and MongoDB test databases alongside PostgreSQL
"""
import sys
import os
import subprocess
import time

print("=" * 80)
print("MULTI-DATABASE SETUP FOR CARELOCK SYNC")
print("=" * 80)
print()

# ══════════════════════════════════════════════════════════════════════════
# Step 1: Check if MySQL and MongoDB are installed
# ══════════════════════════════════════════════════════════════════════════
print("[1/5] Checking Database Installations...")
print()

def check_command(cmd, name):
    """Check if a command exists"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

# Check MySQL
mysql_installed = check_command("mysql --version", "MySQL")
if mysql_installed:
    print("  [OK] MySQL is installed")
else:
    print("  [WARN] MySQL not found")
    print("        Download from: https://dev.mysql.com/downloads/installer/")
    print("        Or install via: choco install mysql")

# Check MongoDB
mongo_installed = check_command("mongod --version", "MongoDB")
if mongo_installed:
    print("  [OK] MongoDB is installed")
else:
    print("  [WARN] MongoDB not found")
    print("        Download from: https://www.mongodb.com/try/download/community")
    print("        Or install via: choco install mongodb")

# Check PostgreSQL (should already exist)
postgres_installed = check_command("psql --version", "PostgreSQL")
if postgres_installed:
    print("  [OK] PostgreSQL is installed")
else:
    print("  [ERROR] PostgreSQL not found - required!")
    sys.exit(1)

print()

# ══════════════════════════════════════════════════════════════════════════
# Step 2: Install Python drivers
# ══════════════════════════════════════════════════════════════════════════
print("[2/5] Installing Python Database Drivers...")
print()

drivers = [
    ('pymysql', 'MySQL driver'),
    ('pymongo', 'MongoDB driver'),
    ('psycopg2', 'PostgreSQL driver (already installed)')
]

for package, description in drivers:
    print(f"  Installing {package} ({description})...")
    try:
        subprocess.run(
            f'pip install {package}',
            shell=True,
            check=True,
            capture_output=True
        )
        print(f"    [OK] {package} installed")
    except subprocess.CalledProcessError as e:
        print(f"    [WARN] {package} installation failed: {e}")

print()

# ══════════════════════════════════════════════════════════════════════════
# Step 3: Generate SQL/Scripts for each database
# ══════════════════════════════════════════════════════════════════════════
print("[3/5] Generating Database Setup Scripts...")
print()

# MySQL Schema
mysql_schema = """-- MySQL Hospital Database Schema
DROP DATABASE IF EXISTS hospital_db_mysql;
CREATE DATABASE hospital_db_mysql;
USE hospital_db_mysql;

-- Patients table
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
) ENGINE=InnoDB;

-- Encounters table
CREATE TABLE encounters (
    encounter_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    encounter_type VARCHAR(50) NOT NULL,
    admission_date DATETIME NOT NULL,
    discharge_date DATETIME,
    chief_complaint TEXT,
    diagnosis TEXT,
    attending_physician VARCHAR(200),
    department VARCHAR(100),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    INDEX idx_patient (patient_id),
    INDEX idx_admission (admission_date)
) ENGINE=InnoDB;

-- Change log table (for CDC)
CREATE TABLE data_change_log (
    change_id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    record_id INT,
    old_data JSON,
    new_data JSON,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_name VARCHAR(100),
    INDEX idx_table (table_name),
    INDEX idx_time (changed_at)
) ENGINE=InnoDB;

-- Insert sample data
INSERT INTO patients (medical_record_number, first_name, last_name, date_of_birth, gender, phone_number, email, city, state)
VALUES 
    ('MRN-MYSQL-001', 'Ahmed', 'Khan', '1985-03-15', 'male', '0300-1234567', 'ahmed.khan@email.com', 'Lahore', 'Punjab'),
    ('MRN-MYSQL-002', 'Fatima', 'Ali', '1990-07-22', 'female', '0321-9876543', 'fatima.ali@email.com', 'Karachi', 'Sindh'),
    ('MRN-MYSQL-003', 'Hassan', 'Ahmed', '1978-11-30', 'male', '0333-5555555', 'hassan.ahmed@email.com', 'Islamabad', 'ICT'),
    ('MRN-MYSQL-004', 'Ayesha', 'Malik', '1995-01-10', 'female', '0345-7777777', 'ayesha.malik@email.com', 'Rawalpindi', 'Punjab'),
    ('MRN-MYSQL-005', 'Usman', 'Iqbal', '1982-05-18', 'male', '0300-9999999', 'usman.iqbal@email.com', 'Faisalabad', 'Punjab');

INSERT INTO encounters (patient_id, encounter_type, admission_date, chief_complaint, diagnosis, attending_physician, department, status)
VALUES
    (1, 'Inpatient', '2026-02-01 10:00:00', 'Fever and cough', 'Pneumonia', 'Dr. Saeed', 'Internal Medicine', 'completed'),
    (2, 'Outpatient', '2026-02-02 14:30:00', 'Routine checkup', 'Hypertension', 'Dr. Nadia', 'Cardiology', 'completed'),
    (3, 'Emergency', '2026-02-03 08:15:00', 'Chest pain', 'Acute MI', 'Dr. Bilal', 'Emergency', 'active');

SELECT 'MySQL database created successfully' AS status;
"""

# Save MySQL schema
with open('C:\\Projects\\CareLock-Sync\\scripts\\setup_mysql.sql', 'w') as f:
    f.write(mysql_schema)
print("  [OK] MySQL schema saved to: scripts/setup_mysql.sql")

# MongoDB setup script
mongodb_setup = """
// MongoDB Hospital Database Setup
use hospital_db_mongodb

// Drop existing collections
db.patients.drop()
db.encounters.drop()
db.change_log.drop()

// Create patients collection with sample data
db.patients.insertMany([
    {
        patient_id: 1,
        medical_record_number: "MRN-MONGO-001",
        first_name: "Zainab",
        last_name: "Hassan",
        date_of_birth: ISODate("1988-04-12"),
        gender: "female",
        blood_type: "O+",
        phone_number: "0300-1111111",
        email: "zainab.hassan@email.com",
        address: {
            line1: "123 Main Street",
            city: "Peshawar",
            state: "KPK",
            zip_code: "25000"
        },
        created_at: new Date(),
        updated_at: new Date()
    },
    {
        patient_id: 2,
        medical_record_number: "MRN-MONGO-002",
        first_name: "Omar",
        last_name: "Farooq",
        date_of_birth: ISODate("1992-09-25"),
        gender: "male",
        blood_type: "A+",
        phone_number: "0321-2222222",
        email: "omar.farooq@email.com",
        address: {
            line1: "456 Park Road",
            city: "Multan",
            state: "Punjab",
            zip_code: "60000"
        },
        created_at: new Date(),
        updated_at: new Date()
    },
    {
        patient_id: 3,
        medical_record_number: "MRN-MONGO-003",
        first_name: "Sara",
        last_name: "Jamil",
        date_of_birth: ISODate("1980-12-05"),
        gender: "female",
        blood_type: "B+",
        phone_number: "0333-3333333",
        email: "sara.jamil@email.com",
        address: {
            line1: "789 Garden Avenue",
            city: "Quetta",
            state: "Balochistan",
            zip_code: "87300"
        },
        created_at: new Date(),
        updated_at: new Date()
    }
])

// Create encounters collection
db.encounters.insertMany([
    {
        encounter_id: 1,
        patient_id: 1,
        encounter_type: "Inpatient",
        admission_date: ISODate("2026-01-28T09:00:00Z"),
        discharge_date: ISODate("2026-01-30T16:00:00Z"),
        chief_complaint: "Severe headache",
        diagnosis: "Migraine",
        attending_physician: "Dr. Asma",
        department: "Neurology",
        status: "completed",
        created_at: new Date()
    },
    {
        encounter_id: 2,
        patient_id: 2,
        encounter_type: "Outpatient",
        admission_date: ISODate("2026-02-01T11:00:00Z"),
        chief_complaint: "Diabetes followup",
        diagnosis: "Type 2 Diabetes",
        attending_physician: "Dr. Kamran",
        department: "Endocrinology",
        status: "completed",
        created_at: new Date()
    }
])

// Create indexes
db.patients.createIndex({ medical_record_number: 1 }, { unique: true })
db.patients.createIndex({ last_name: 1 })
db.encounters.createIndex({ patient_id: 1 })
db.encounters.createIndex({ admission_date: -1 })

// Create change log collection
db.change_log.createIndex({ table_name: 1, changed_at: -1 })

print("MongoDB database created successfully")
"""

# Save MongoDB script
with open('C:\\Projects\\CareLock-Sync\\scripts\\setup_mongodb.js', 'w') as f:
    f.write(mongodb_setup)
print("  [OK] MongoDB script saved to: scripts/setup_mongodb.js")

print()

# ══════════════════════════════════════════════════════════════════════════
# Step 4: Instructions for manual setup
# ══════════════════════════════════════════════════════════════════════════
print("[4/5] Database Setup Instructions")
print()
print("=" * 80)
print("MANUAL SETUP REQUIRED")
print("=" * 80)
print()

if mysql_installed:
    print("MySQL Setup:")
    print("  1. Open Command Prompt as Administrator")
    print("  2. Run: mysql -u root -p < C:\\Projects\\CareLock-Sync\\scripts\\setup_mysql.sql")
    print("  3. Or use MySQL Workbench to execute the SQL file")
    print("  4. Default credentials: root / (your MySQL password)")
    print()
else:
    print("MySQL NOT INSTALLED - Skipping MySQL setup")
    print()

if mongo_installed:
    print("MongoDB Setup:")
    print("  1. Ensure MongoDB service is running")
    print("     - Run: net start MongoDB")
    print("  2. Open Command Prompt")
    print("  3. Run: mongosh < C:\\Projects\\CareLock-Sync\\scripts\\setup_mongodb.js")
    print("  4. Or use MongoDB Compass to execute the script")
    print()
else:
    print("MongoDB NOT INSTALLED - Skipping MongoDB setup")
    print()

print("PostgreSQL Setup:")
print("  Already configured - using existing hospital_db")
print()

# ══════════════════════════════════════════════════════════════════════════
# Step 5: Create connection strings
# ══════════════════════════════════════════════════════════════════════════
print("[5/5] Creating Connection Configuration...")
print()

connection_config = """# Multi-Database Connection Strings
# Add these to your .env file or use directly in tests

# PostgreSQL (existing)
POSTGRES_URL=postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db

# MySQL (new)
MYSQL_URL=mysql+pymysql://root:YOUR_MYSQL_PASSWORD@localhost:3306/hospital_db_mysql

# MongoDB (new)
MONGODB_URL=mongodb://localhost:27017/hospital_db_mongodb

# Usage in Python:
# from sqlalchemy import create_engine
# mysql_engine = create_engine(MYSQL_URL)
# 
# from pymongo import MongoClient
# mongo_client = MongoClient(MONGODB_URL)
"""

with open('C:\\Projects\\CareLock-Sync\\config\\multi_db_connections.env', 'w') as f:
    f.write(connection_config)
print("  [OK] Connection config saved to: config/multi_db_connections.env")

print()
print("=" * 80)
print("SETUP SCRIPT COMPLETE")
print("=" * 80)
print()
print("Next Steps:")
print("  1. Execute the SQL/JS files manually (see instructions above)")
print("  2. Update MySQL password in config/multi_db_connections.env")
print("  3. Run: python scripts/test_multi_database.py")
print()
print("=" * 80)
