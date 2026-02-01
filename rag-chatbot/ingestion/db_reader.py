import psycopg2
import json

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5434",
        database="carelock",
        user="carelock_user",
        password="carelock_pass"
    )

def fetch_data_for_rag():
    conn = get_connection()
    cur = conn.cursor()

    # 1. Fetch all Patients to create a lookup map (ID -> Name)
    cur.execute("SELECT id, resource FROM fhir_patient;")
    patient_rows = cur.fetchall()
    
    patient_map = {}
    documents = []

    print(f"   -> Found {len(patient_rows)} patients.")
    
    for pid, resource in patient_rows:
        # Extract Name
        name = resource.get("name", [{}])[0].get("text", "Unknown")
        dob = resource.get("birthDate", "Unknown")
        gender = resource.get("gender", "Unknown")
        
        # Store in map for linking later
        patient_map[f"Patient/{pid}"] = name
        
        # Add Patient Identity Doc
        doc = (f"Patient Record:\nName: {name}\nGender: {gender}\nDOB: {dob}")
        documents.append(doc)

    # 2. Fetch Observations (Labs) and link to Patient Names
    cur.execute("SELECT resource FROM fhir_observation;")
    obs_rows = cur.fetchall()
    
    print(f"   -> Found {len(obs_rows)} lab observations.")

    for (resource,) in obs_rows:
        # Find who this belongs to
        subject_ref = resource.get("subject", {}).get("reference", "")
        patient_name = patient_map.get(subject_ref, "Unknown Patient")
        
        test_name = resource.get("code", {}).get("text", "Unknown Test")
        result = resource.get("valueString", "Unknown Result")
        date = resource.get("effectiveDateTime", "")

        # Create a clinical sentence
        doc = (f"Lab Result for {patient_name}:\n"
               f"Test: {test_name}\n"
               f"Result: {result}\n"
               f"Date: {date}")
        documents.append(doc)

    conn.close()
    return documents

if __name__ == "__main__":
    docs = fetch_data_for_rag()
    print("\n--- PREVIEW OF DOCUMENTS ---")
    for d in docs:
        print(d)
        print("-" * 20)