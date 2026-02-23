"""Full RAG endpoint test — corrected field names."""
import sys, os
os.environ["PYTHONIOENCODING"] = "utf-8"
import requests, time

BASE  = "http://localhost:8000"
ADMIN = "clk-admin-change-me-in-prod"
H     = {"X-API-Key": ADMIN}

def chk(label, r):
    ok = "PASS" if r.status_code == 200 else "FAIL"
    print(f"[{ok}] {label} -> HTTP {r.status_code}")
    if r.status_code != 200:
        print(f"      {r.text[:300]}")
    return r

print("=" * 60)
print("RAG SPRINT 4 — FULL TEST (models pre-warmed)")
print("=" * 60)

# 1. Status
r = chk("GET /rag/status", requests.get(f"{BASE}/api/v1/rag/status", headers=H, timeout=30))
if r.status_code == 200:
    d = r.json()
    print(f"      ollama_running = {d.get('ollama_running')}")
    print(f"      ready          = {d.get('ready')}")
    print(f"      llm_model      = {d.get('llm_model')}")
    print(f"      mappings       = {d.get('vector_store', {}).get('total_mappings')}")

# 2. Models
r = chk("GET /rag/models", requests.get(f"{BASE}/api/v1/rag/models", headers=H, timeout=15))
if r.status_code == 200:
    d = r.json()
    print(f"      active   = {d.get('active')}")
    print(f"      all      = {d.get('models')}")

# 3. Knowledge base
r = chk("GET /rag/knowledge-base", requests.get(f"{BASE}/api/v1/rag/knowledge-base", headers=H, timeout=15))
if r.status_code == 200:
    d = r.json()
    print(f"      {d}")

# 4. suggest/field
print(f"\n--- suggest/field: patient_id integer ---")
t0 = time.time()
r = requests.post(f"{BASE}/api/v1/rag/suggest/field", headers=H, timeout=120,
                  json={"field_name":"patient_id","field_type":"integer",
                        "fhir_resource":"Patient","sample_values":["1001","1002"]})
elapsed = round(time.time() - t0, 1)
print(f"[{'PASS' if r.status_code==200 else 'FAIL'}] suggest/field -> HTTP {r.status_code} ({elapsed}s)")
if r.status_code == 200:
    d = r.json()
    print(f"      target_path    = {d.get('target_path')}")
    print(f"      confidence     = {d.get('confidence')}")
    print(f"      reasoning      = {d.get('reasoning')}")
    print(f"      transformation = {d.get('transformation')}")
    similar = d.get("similar_mappings", [])
    print(f"      similar_maps   = {len(similar)} returned")
    for s in similar[:3]:
        print(f"        {s.get('source_field')} -> {s.get('target_path')} (sim={s.get('similarity')})")

# 5. suggest/field — date_of_birth
print(f"\n--- suggest/field: date_of_birth date ---")
t0 = time.time()
r = requests.post(f"{BASE}/api/v1/rag/suggest/field", headers=H, timeout=120,
                  json={"field_name":"date_of_birth","field_type":"date",
                        "fhir_resource":"Patient","sample_values":["1990-05-15"]})
elapsed = round(time.time() - t0, 1)
print(f"[{'PASS' if r.status_code==200 else 'FAIL'}] suggest/field -> HTTP {r.status_code} ({elapsed}s)")
if r.status_code == 200:
    d = r.json()
    print(f"      target_path = {d.get('target_path')} | confidence = {d.get('confidence')}")
    similar = d.get("similar_mappings", [])
    print(f"      similar_maps = {len(similar)}")

# 6. suggest/schema (uses 'columns' not 'fields')
print(f"\n--- suggest/schema: encounter table ---")
t0 = time.time()
r = requests.post(f"{BASE}/api/v1/rag/suggest/schema", headers=H, timeout=300,
                  json={"table_name":"encounters",
                        "columns":[
                            {"name":"encounter_id","type":"integer"},
                            {"name":"admit_date","type":"date"},
                            {"name":"discharge_date","type":"date"},
                        ],
                        "fhir_resource":"Encounter"})
elapsed = round(time.time() - t0, 1)
print(f"[{'PASS' if r.status_code==200 else 'FAIL'}] suggest/schema -> HTTP {r.status_code} ({elapsed}s)")
if r.status_code == 200:
    d = r.json()
    print(f"      table     = {d.get('table_name')}")
    print(f"      accuracy  = {d.get('accuracy_pct')}%")
    for m in d.get("mappings", []):
        print(f"      {m.get('source_field'):<20} -> {m.get('target_path')} (conf={m.get('confidence')})")

# 7. suggest/batch
print(f"\n--- suggest/batch: 3 fields ---")
t0 = time.time()
r = requests.post(f"{BASE}/api/v1/rag/suggest/batch", headers=H, timeout=300,
                  json={"fields":[
                      {"field_name":"drug_name","field_type":"varchar","fhir_resource":"MedicationRequest"},
                      {"field_name":"lab_value","field_type":"decimal","fhir_resource":"Observation"},
                  ]})
elapsed = round(time.time() - t0, 1)
print(f"[{'PASS' if r.status_code==200 else 'FAIL'}] suggest/batch -> HTTP {r.status_code} ({elapsed}s)")
if r.status_code == 200:
    for item in r.json().get("results", []):
        print(f"      {item.get('field_name'):<20} -> {item.get('target_path')} (conf={item.get('confidence')})")

# 8. POST /rag/mappings
r = chk("POST /rag/mappings", requests.post(f"{BASE}/api/v1/rag/mappings", headers=H, timeout=15,
    json={"source_field":"custom_mrn","source_type":"varchar",
          "target_path":"Patient.identifier[0].value",
          "fhir_resource":"Patient","confidence":0.99}))
if r.status_code == 200:
    print(f"      {r.json().get('message')}")

# 9. confirm endpoint
r = chk("POST /rag/confirm", requests.post(f"{BASE}/api/v1/rag/confirm", headers=H, timeout=15,
    json={"source_field":"patient_mrn","source_type":"varchar",
          "target_path":"Patient.identifier[0].value",
          "fhir_resource":"Patient"}))
if r.status_code == 200:
    print(f"      {r.json().get('message')}")

# 10. Clinical chat
print(f"\n--- /rag/chat: grounded clinical Q&A ---")
t0 = time.time()
r = requests.post(f"{BASE}/api/v1/rag/chat", headers=H, timeout=120,
                  json={"question":"How many patients are in the system and what is the average data quality score?"})
elapsed = round(time.time() - t0, 1)
print(f"[{'PASS' if r.status_code==200 else 'FAIL'}] /rag/chat -> HTTP {r.status_code} ({elapsed}s)")
if r.status_code == 200:
    d = r.json()
    print(f"      grounded = {d.get('grounded')}")
    print(f"      answer   = {d.get('answer', '')[:200]}")
    ctx = d.get("context_used", {})
    print(f"      context  = patients={ctx.get('total_patients')} avg_score={ctx.get('avg_completeness')}")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
