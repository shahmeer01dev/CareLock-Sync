"""
Test CDC by making a database change
"""
import psycopg2
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.config import settings

# Connect to database
conn = psycopg2.connect(settings.hospital_db_url)
cur = conn.cursor()

# Make a test change
print("Making test update to trigger CDC...")
cur.execute("""
    UPDATE patients 
    SET email = 'updated.email@example.com' 
    WHERE patient_id = 3
""")

conn.commit()
print("[OK] Patient record updated successfully")
print("CDC trigger should have logged this change")

# Close connection
cur.close()
conn.close()

print("\nNow check for changes via API:")
print("GET http://localhost:8000/api/v1/connector/cdc/changes")
