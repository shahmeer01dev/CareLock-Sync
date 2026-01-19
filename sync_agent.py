import requests
import time

# --- CONFIGURATION ---
LOCAL_CONNECTOR_URL = "http://localhost:8000"
CENTRAL_PLATFORM_URL = "http://localhost:8001"
TENANT_ID = "hospital_01"
API_TOKEN = "CARELOCK_SECURE_TOKEN_123"

HEADERS = {
    "Authorization": API_TOKEN,
    "Content-Type": "application/json"
}

def sync_patients():
    print(f"[*] Fetching Patients from {LOCAL_CONNECTOR_URL}...")
    try:
        response = requests.get(f"{LOCAL_CONNECTOR_URL}/fhir/patients")
        patients = response.json()
        
        print(f" -> Found {len(patients)} patients. Syncing to Cloud...")
        
        for p in patients:
            # Push to Central Platform
            res = requests.post(
                f"{CENTRAL_PLATFORM_URL}/ingest/patient/{TENANT_ID}",
                json=p,
                headers=HEADERS
            )
            if res.status_code == 200:
                print(f"    [+] Synced Patient: {p['id']}")
            else:
                print(f"    [!] Failed to sync Patient {p['id']}: {res.text}")
                
    except Exception as e:
        print(f"[!] Error syncing patients: {e}")

def sync_encounters():
    print(f"[*] Fetching Encounters...")
    try:
        response = requests.get(f"{LOCAL_CONNECTOR_URL}/fhir/encounters")
        encounters = response.json()
        
        print(f" -> Found {len(encounters)} encounters. Syncing...")
        
        for e in encounters:
            res = requests.post(
                f"{CENTRAL_PLATFORM_URL}/ingest/encounter/{TENANT_ID}",
                json=e,
                headers=HEADERS
            )
            if res.status_code == 200:
                print(f"    [+] Synced Encounter: {e['id']}")
            else:
                print(f"    [!] Failed {e['id']}: {res.text}")

    except Exception as e:
        print(f"[!] Error syncing encounters: {e}")

def sync_observations():
    print(f"[*] Fetching Lab Observations...")
    try:
        response = requests.get(f"{LOCAL_CONNECTOR_URL}/fhir/observations")
        observations = response.json()
        
        print(f" -> Found {len(observations)} labs. Syncing...")
        
        for o in observations:
            res = requests.post(
                f"{CENTRAL_PLATFORM_URL}/ingest/observation/{TENANT_ID}",
                json=o,
                headers=HEADERS
            )
            if res.status_code == 200:
                print(f"    [+] Synced Lab Result: {o['id']}")
            else:
                print(f"    [!] Failed {o['id']}: {res.text}")

    except Exception as e:
        print(f"[!] Error syncing observations: {e}")

if __name__ == "__main__":
    print("=== CareLock Sync Agent Started ===")
    
    # 1. Sync Patients
    sync_patients()
    
    # 2. Sync Encounters
    sync_encounters()
    
    # 3. Sync Observations
    sync_observations()
    
    print("=== Sync Complete ===")