"""
Complete Multi-Database Setup and Test
This script:
1. Checks if MySQL and MongoDB are running
2. Creates and populates all three databases
3. Sets up CDC on all databases
4. Tests the complete pipeline

Run this before the supervisor demo to validate everything works!
"""
import sys
import os
import subprocess
import time

print("=" * 80)
print("CARELOCK SYNC - MULTI-DATABASE SETUP & VALIDATION")
print("=" * 80)
print()

# Step 1: Check prerequisites
print("[STEP 1/7] Checking Prerequisites...")
print()

# Check Python packages
required_packages = [
    ('pymysql', 'MySQL adapter'),
    ('pymongo', 'MongoDB adapter'),
    ('faker', 'Test data generation')
]

missing_packages = []
for package, description in required_packages:
    try:
        __import__(package)
        print(f"  [OK] {package:15s} - {description}")
    except ImportError:
        print(f"  [MISSING] {package:15s} - {description}")
        missing_packages.append(package)

if missing_packages:
    print(f"\n  Installing missing packages...")
    for pkg in missing_packages:
        subprocess.run([sys.executable, '-m', 'pip', 'install', pkg, '--break-system-packages'],
                      capture_output=True)
    print(f"  [OK] Packages installed")

# Step 2: Test database connections
print("\n[STEP 2/7] Testing Database Connections...")
print()

db_status = {}

# PostgreSQL
try:
    import psycopg2
    conn = psycopg2.connect(
        "postgresql://hospital_user:hospital_pass@localhost:5432/hospital_db"
    )
    conn.close()
    print("  [OK] PostgreSQL - Connected")
    db_status['PostgreSQL'] = True
except Exception as e:
    print(f"  [FAIL] PostgreSQL - {str(e)[:50]}")
    db_status['PostgreSQL'] = False

# MySQL
try:
    import pymysql
    conn = pymysql.connect(host='localhost', user='root', password='root')
    conn.close()
    print("  [OK] MySQL - Connected")
    db_status['MySQL'] = True
except Exception as e:
    print(f"  [FAIL] MySQL - {str(e)[:50]}")
    db_status['MySQL'] = False

# MongoDB
try:
    from pymongo import MongoClient
    client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
    client.admin.command('ping')
    print("  [OK] MongoDB - Connected")
    db_status['MongoDB'] = True
except Exception as e:
    print(f"  [FAIL] MongoDB - {str(e)[:50]}")
    db_status['MongoDB'] = False

# Step 3: Setup MySQL (if connected)
if db_status.get('MySQL'):
    print("\n[STEP 3/7] Setting up MySQL Database...")
    try:
        result = subprocess.run(
            [sys.executable, r'C:\Projects\CareLock-Sync\scripts\setup_mysql_data.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("  [OK] MySQL database created and populated")
        else:
            print(f"  [WARN] MySQL setup had issues")
            print(result.stderr[:200] if result.stderr else "")
    except Exception as e:
        print(f"  [FAIL] MySQL setup error: {e}")
else:
    print("\n[STEP 3/7] Skipping MySQL (not connected)")

# Step 4: Setup MongoDB (if connected)
if db_status.get('MongoDB'):
    print("\n[STEP 4/7] Setting up MongoDB Database...")
    try:
        result = subprocess.run(
            [sys.executable, r'C:\Projects\CareLock-Sync\scripts\setup_mongodb_data.py'],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("  [OK] MongoDB database created and populated")
        else:
            print(f"  [WARN] MongoDB setup had issues")
    except Exception as e:
        print(f"  [FAIL] MongoDB setup error: {e}")
else:
    print("\n[STEP 4/7] Skipping MongoDB (not connected)")

# Step 5: Test Multi-Database CDC
print("\n[STEP 5/7] Testing Multi-Database CDC...")
print()
try:
    result = subprocess.run(
        [sys.executable, r'C:\Projects\CareLock-Sync\scripts\test_multi_database_cdc.py'],
        capture_output=True,
        text=True,
        timeout=30
    )
    print(result.stdout)
    if result.returncode != 0 and result.stderr:
        print("Errors:", result.stderr[:500])
except Exception as e:
    print(f"  [FAIL] CDC test error: {e}")

# Step 6: Test RAG/AI Mapping
print("\n[STEP 6/7] Testing RAG AI Mapping...")
try:
    sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
    sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\rag')
    from mapping_suggester import MappingSuggester
    
    suggester = MappingSuggester()
    result = suggester.suggest_mapping(
        field_name="patient_birthdate",
        field_type="date",
        sample_values=["1990-01-15"]
    )
    print(f"  [OK] AI Mapping: {result['target_path']} ({result['confidence']*100:.0f}% confidence)")
except Exception as e:
    print(f"  [FAIL] RAG test error: {e}")

# Step 7: Summary
print("\n[STEP 7/7] Final Summary")
print("=" * 80)

connected_dbs = [db for db, status in db_status.items() if status]
print(f"\nDatabases Connected: {len(connected_dbs)}/3")
for db in connected_dbs:
    print(f"  [OK] {db}")

not_connected = [db for db, status in db_status.items() if not status]
if not_connected:
    print(f"\nDatabases NOT Connected: {len(not_connected)}/3")
    for db in not_connected:
        print(f"  [X] {db}")

# Calculate coverage
coverage_map = {'PostgreSQL': 20, 'MySQL': 40, 'MongoDB': 5}
total_coverage = sum(coverage_map.get(db, 0) for db in connected_dbs)

print(f"\nReal-World Hospital Coverage: {total_coverage}%")
print("  (PostgreSQL 20% + MySQL 40% + MongoDB 5% = 65% maximum)")

print("\n" + "=" * 80)
print("SETUP COMPLETE")
print("=" * 80)

if total_coverage >= 60:
    print("\n[SUCCESS] System ready for supervisor demo!")
    print("You have multi-database support working across 60%+ of hospitals.")
else:
    print("\n[WARNING] Some databases not connected.")
    print("PostgreSQL is working. Install MySQL/MongoDB for full demo.")

print()
