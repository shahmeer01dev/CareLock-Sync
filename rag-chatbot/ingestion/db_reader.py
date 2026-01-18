import psycopg2

# Connection to Central FHIR Database
def get_connection():
    return psycopg2.connect(
        host="localhost",
        port="5434",
        database="carelock",
        user="carelock_user",
        password="carelock_pass"
    )

def fetch_fhir_patients():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT resource FROM fhir_patient;")
    rows = cur.fetchall()

    conn.close()
    return rows

def fhir_patient_to_text(patient):
    """
    Convert FHIR Patient resource to readable clinical text
    """
    name = patient.get("name", [{}])[0].get("text", "Unknown")
    gender = patient.get("gender", "Unknown")
    dob = patient.get("birthDate", "Unknown")

    text = (
        f"Patient Name: {name}\n"
        f"Gender: {gender}\n"
        f"Date of Birth: {dob}\n"
    )
    return text

if __name__ == "__main__":
    patients = fetch_fhir_patients()

    print("\n--- FHIR PATIENT RECORDS ---\n")

    for row in patients:
        patient_resource = row[0]   # JSONB comes as dict
        readable_text = fhir_patient_to_text(patient_resource)
        print(readable_text)
        print("-" * 40)
