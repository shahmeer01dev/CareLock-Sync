"""
Sprint 4 -- Full RAG Test Suite
Tests: status, field mapping accuracy, schema mapping, clinical chat, knowledge base
Run: python test_sprint4_rag.py
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))
# Force UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import requests

BASE  = "http://localhost:8000"
KEY   = "clk-admin-change-me-in-prod"
H     = {"X-API-Key": KEY, "Content-Type": "application/json"}

def req(method, path, body=None):
    url = BASE + path
    r   = requests.request(method, url, headers=H, json=body, timeout=180)
    return r.status_code, r.json()

PASS = 0; FAIL = 0

def check(label, condition, detail=""):
    global PASS, FAIL
    mark = "PASS" if condition else "FAIL"
    if condition: PASS += 1
    else: FAIL += 1
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{mark}] {label}{suffix}")

print("=" * 62)
print(" SPRINT 4 — RAG SYSTEM FULL TEST SUITE")
print("=" * 62)

# ── T1: RAG Status ───────────────────────────────────────────
print("\n[T1] RAG System Status")
code, r = req("GET", "/api/v1/rag/status")
check("HTTP 200",              code == 200)
check("Ollama running",        r.get("ollama_running") == True)
check("llama3.2 model active", "llama3.2" in r.get("llm_model", ""))
check("ChromaDB backend",      r.get("vector_store", {}).get("backend") == "chromadb")
mappings_count = r.get("vector_store", {}).get("total_mappings", 0)
check("41 FHIR mappings loaded", mappings_count >= 41, f"{mappings_count} mappings")
check("RAG ready",             r.get("ready") == True)

# ── T2: Models ───────────────────────────────────────────────
print("\n[T2] Ollama Model Listing")
code, r = req("GET", "/api/v1/rag/models")
check("HTTP 200",              code == 200)
check("llama3.2:3b present",   any("llama3.2" in m for m in r.get("models", [])))
check("nomic-embed-text present", any("nomic-embed" in m for m in r.get("models", [])))

# ── T3: Known-field mapping accuracy ────────────────────────
print("\n[T3] FHIR Field Mapping Accuracy (7 known fields)")
TEST_FIELDS = [
    ("patient_id",      "integer", "Patient",           "id"),
    ("date_of_birth",   "date",    "Patient",           "birthDate"),
    ("first_name",      "string",  "Patient",           "name"),
    ("phone_number",    "string",  "Patient",           "telecom"),
    ("admission_date",  "dateTime","Encounter",         "period"),
    ("result_value",    "decimal", "Observation",       "valueQuantity"),
    ("medication_name", "string",  "MedicationRequest", "medicationCodeableConcept"),
]
correct = 0
for fname, ftype, resource, expected_fragment in TEST_FIELDS:
    t0   = time.time()
    code, r = req("POST", "/api/v1/rag/suggest/field", {
        "field_name": fname, "field_type": ftype, "fhir_resource": resource
    })
    ms   = round((time.time()-t0)*1000)
    got  = r.get("target_path","") or ""
    conf = round(r.get("confidence",0)*100)
    ok   = expected_fragment.lower() in got.lower()
    if ok: correct += 1
    print(f"  [{'PASS' if ok else 'FAIL'}] {fname:<22} -> {got:<40} conf={conf}%  ({ms}ms)")

accuracy = round(correct / len(TEST_FIELDS) * 100)
check(f"Accuracy ≥ 70% ({accuracy}%)", accuracy >= 70, f"{correct}/{len(TEST_FIELDS)}")

# ── T4: Unknown-field mapping (variant names) ────────────────
print("\n[T4] Unknown/Variant Field Mapping (AI generalisation)")
VARIANT_FIELDS = [
    ("dob",             "date",    "Patient",    "birth"),
    ("fname",           "string",  "Patient",    "name"),
    ("mobile",          "string",  "Patient",    "telecom"),
    ("test_result",     "decimal", "Observation","valueQuantity"),
]
variant_correct = 0
for fname, ftype, resource, frag in VARIANT_FIELDS:
    code, r = req("POST", "/api/v1/rag/suggest/field", {
        "field_name": fname, "field_type": ftype, "fhir_resource": resource
    })
    got  = r.get("target_path","") or ""
    conf = round(r.get("confidence",0)*100)
    ok   = frag.lower() in got.lower()
    if ok: variant_correct += 1
    print(f"  [{'PASS' if ok else '~   '}] {fname:<22} → {got:<35} conf={conf}%")
print(f"  Generalisation: {variant_correct}/{len(VARIANT_FIELDS)} variant fields mapped correctly")

# ── T5: Schema-level mapping (patients table) ────────────────
print("\n[T5] Full Schema Mapping — patients table")
t0 = time.time()
code, r = req("POST", "/api/v1/rag/suggest/schema", {
    "table_name": "patients",
    "fhir_resource": "Patient",
    "columns": [
        {"name": "patient_id",   "type": "integer"},
        {"name": "first_name",   "type": "string"},
        {"name": "last_name",    "type": "string"},
        {"name": "date_of_birth","type": "date"},
        {"name": "gender",       "type": "string"},
        {"name": "phone_number", "type": "string"},
        {"name": "email",        "type": "string"},
        {"name": "city",         "type": "string"},
    ]
})
ms = round((time.time()-t0)*1000)
check("HTTP 200",              code == 200)
stats  = r.get("statistics", {})
schema_acc = r.get("accuracy_pct", 0)
check(f"Schema accuracy ≥ 70% ({schema_acc}%)", schema_acc >= 70)
check("Stats returned",        stats.get("total", 0) > 0, f"total={stats.get('total',0)}")
print(f"  Accuracy: {schema_acc}%  high={stats.get('high',0)}  medium={stats.get('medium',0)}  low={stats.get('low',0)}  ({ms}ms)")

# ── T6: Confirm & Learn mapping ──────────────────────────────
print("\n[T6] Confirm Mapping (RAG learning)")
code, r = req("POST", "/api/v1/rag/confirm", {
    "source_field": "mrn_number",
    "source_type":  "string",
    "target_path":  "identifier[0].value",
    "fhir_resource":"Patient",
    "transformation":"none"
})
check("HTTP 200",              code == 200)
check("Saved=True",            r.get("saved") == True)# Now query it back
_, r2 = req("GET", "/api/v1/rag/knowledge-base")
new_count = r2.get("vector_store", {}).get("total_mappings", 0)
check("Count increased",       new_count > mappings_count, f"now {new_count}")

# ── T7: Clinical Chat — grounded Q&A ────────────────────────
print("\n[T7] Clinical Chat (Ollama Q&A grounded in FHIR DB)")
CHAT_QUESTIONS = [
    ("How many patients are in the system?",           ["patient","total","114","113"]),
    ("What is the gender distribution of patients?",   ["male","female","gender"]),
    ("What is the data quality breakdown?",            ["quality","high","score","complete"]),
]
chat_ok = 0
for question, keywords in CHAT_QUESTIONS:
    t0 = time.time()
    code, r = req("POST", "/api/v1/rag/chat", {"question": question})
    ms   = round((time.time()-t0)*1000)
    ans  = (r.get("answer") or "").lower()
    grounded = r.get("grounded", False)
    has_kw   = any(kw.lower() in ans for kw in keywords)
    ok = code == 200 and grounded and has_kw
    if ok: chat_ok += 1
    print(f"  [{'PASS' if ok else 'FAIL'}] Q: {question[:50]}")
    print(f"        A: {ans[:100]}...")
    print(f"        grounded={grounded}  keywords_found={has_kw}  ({ms}ms)")
check(f"Chat accuracy {chat_ok}/{len(CHAT_QUESTIONS)}", chat_ok >= 2)

# ── Summary ──────────────────────────────────────────────────
total = PASS + FAIL
print("\n" + "=" * 62)
print(f" RESULTS: {PASS}/{total} PASSED  ({round(PASS/total*100)}%)")
print(f" Mapping accuracy:  {accuracy}%  (target: >85%)")
print(f" Schema accuracy:   {schema_acc}%")
print(f" Chat accuracy:     {chat_ok}/{len(CHAT_QUESTIONS)}")
print(f" Vector store:      {new_count} mappings")
print(f" Model:             llama3.2:3b (fully local, no API key)")
print("=" * 62)
