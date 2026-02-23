import requests, json

BASE = "http://localhost:8000"
H    = {"X-API-Key": "clk-admin-change-me-in-prod"}

def hit(url, method="GET", body=None, timeout=180):
    try:
        if method == "POST":
            r = requests.post(url, headers=H, json=body, timeout=timeout)
        else:
            r = requests.get(url, headers=H, timeout=timeout)
        print(f"HTTP {r.status_code}: {r.text[:400]}")
    except Exception as e:
        print(f"ERROR: {e}")

print("\n=== RAG/status ===")
hit(f"{BASE}/api/v1/rag/status")

print("\n=== RAG/models ===")
hit(f"{BASE}/api/v1/rag/models")

print("\n=== RAG/knowledge-base ===")
hit(f"{BASE}/api/v1/rag/knowledge-base")

print("\n=== RAG/suggest/field (patient_id) ===")
hit(f"{BASE}/api/v1/rag/suggest/field", "POST",
    {"field_name": "patient_id", "field_type": "integer", "fhir_resource": "Patient"})

print("\n=== RAG/suggest/field (date_of_birth) ===")
hit(f"{BASE}/api/v1/rag/suggest/field", "POST",
    {"field_name": "date_of_birth", "field_type": "date", "fhir_resource": "Patient"})
