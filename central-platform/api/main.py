from fastapi import FastAPI
import psycopg2
import json

app = FastAPI(title="CareLock Central API")

def get_conn():
    return psycopg2.connect(
        host="localhost",
        port="5434",
        database="carelock",
        user="carelock_user",
        password="carelock_pass"
    )

@app.post("/ingest/patient/{tenant_id}")
def ingest_patient(tenant_id: str, patient: dict):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO fhir_patient (id, tenant_id, resource) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
        (patient["id"], tenant_id, json.dumps(patient))
    )

    conn.commit()
    conn.close()
    return {"status": "Patient stored"}

@app.post("/ingest/encounter/{tenant_id}")
def ingest_encounter(tenant_id: str, encounter: dict):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO fhir_encounter (id, tenant_id, resource) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
        (encounter["id"], tenant_id, json.dumps(encounter))
    )

    conn.commit()
    conn.close()
    return {"status": "Encounter stored"}

@app.post("/ingest/observation/{tenant_id}")
def ingest_observation(tenant_id: str, observation: dict):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO fhir_observation (id, tenant_id, resource) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
        (observation["id"], tenant_id, json.dumps(observation))
    )

    conn.commit()
    conn.close()
    return {"status": "Observation stored"}
