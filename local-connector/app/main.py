from fastapi import FastAPI
from fhir_mapper import map_patient, map_encounter, map_observation
from db import get_connection

app = FastAPI(title="CareLock Local Connector")

@app.get("/health")
def health_check():
    return {"status": "Local Connector is running"}

@app.get("/schema")
def get_schema():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)

    rows = cur.fetchall()
    conn.close()

    schema = {}
    for table, column, dtype in rows:
        schema.setdefault(table, []).append({
            "column": column,
            "type": dtype
        })

    return schema

@app.get("/patients")
def get_patients():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients;")
    rows = cur.fetchall()
    conn.close()

    return rows

@app.get("/visits")
def get_visits():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM visits;")
    rows = cur.fetchall()
    conn.close()

    return rows

@app.get("/labs")
def get_labs():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM labs;")
    rows = cur.fetchall()
    conn.close()

    return rows

@app.get("/fhir/patients")
def get_fhir_patients():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients;")
    rows = cur.fetchall()
    conn.close()

    return [map_patient(row) for row in rows]


@app.get("/fhir/encounters")
def get_fhir_encounters():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM visits;")
    rows = cur.fetchall()
    conn.close()

    return [map_encounter(row) for row in rows]


@app.get("/fhir/observations")
def get_fhir_observations():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM labs;")
    rows = cur.fetchall()
    conn.close()

    return [map_observation(row) for row in rows]
