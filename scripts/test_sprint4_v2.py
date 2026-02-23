"""
Sprint 4 v2 — Comprehensive Test Suite
Tests dual-model architecture + verification workflow

Run: python scripts\test_sprint4_v2.py
"""
import os, sys, time, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
os.chdir(ROOT)

PASS = "  [PASS]"; FAIL = "  [FAIL]"; SKIP = "  [SKIP]"
results = []

def check(label, ok, detail=""):
    icon = PASS if ok else FAIL
    print(f"{icon} {label}" + (f"  —  {detail}" if detail else ""))
    results.append((label, ok))
    return ok

def banner(t):
    print(f"\n{'─'*64}\n  {t}\n{'─'*64}")

print("\n" + "="*64)
print("  SPRINT 4 v2 — DUAL-MODEL RAG TEST SUITE")
print("="*64)

# T1: Verify file structure
banner("T1 — File Structure")
FILES = [
    "backend/rag/ollama_client.py",
    "backend/rag/fhir_knowledge.py",
    "backend/rag/vector_store.py",
    "backend/rag/mapping_suggester.py",
    "backend/rag/__init__.py",
    "backend/api/routes/rag.py",
    "scripts/review_mappings.py",
    "config/.env",
]
all_present = True
for f in FILES:
    exists = os.path.exists(os.path.join(ROOT, f))
    check(f, exists)
    if not exists: all_present = False

# T2: Environment config
banner("T2 — Environment Configuration")
env_path = os.path.join(ROOT, "config", ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        env = f.read()
    check("MAPPING_MODEL in .env", "MAPPING_MODEL" in env)
    check("CHAT_MODEL in .env",    "CHAT_MODEL" in env)
    check("MAPPING_MODEL=llama3.2:3b", "llama3.2:3b" in env)
    check("CHAT_MODEL=phi3",           "phi3" in env)
else:
    check("config/.env exists", False, "File not found")

# T3: Ollama connectivity
banner("T3 — Ollama Connectivity")
ollama_ok = False
models_present = False
try:
    import requests
    r = requests.get("http://localhost:11434/api/tags", timeout=5)
    models = [m["name"] for m in r.json().get("models", [])]
    check("Ollama daemon reachable", r.status_code == 200, f"HTTP {r.status_code}")
    check("Models installed",        len(models) > 0, str(models))
    
    has_llama = any("llama3.2" in m for m in models)
    has_phi3  = any("phi3" in m for m in models)
    has_nomic = any("nomic" in m for m in models)
    
    check("llama3.2:3b available", has_llama)
    check("phi3 available",        has_phi3)
    check("nomic-embed-text available", has_nomic)
    
    ollama_ok = True
    models_present = has_llama and has_phi3 and has_nomic
except Exception as e:
    check("Ollama daemon reachable", False, str(e))

# T4: MappingSuggester init (dual-model)
banner("T4 — MappingSuggester (Dual-Model)")
suggester = None
if ollama_ok and models_present:
    try:
        from rag.mapping_suggester import MappingSuggester
        suggester = MappingSuggester(
            mapping_model="llama3.2:3b",
            chat_model="phi3",
            vector_store_path=os.path.join(ROOT, "databases", "chroma"),
        )
        stats = suggester.get_stats()
        check("MappingSuggester init",     True)
        check("mapping_model is llama3.2", "llama3.2" in stats["mapping_model"])
        check("chat_model is phi3",        "phi3" in stats["chat_model"])
        check("Mappings loaded > 100",     stats["total_mappings"] > 100,
              f"{stats['total_mappings']} mappings")
    except Exception as e:
        check("MappingSuggester init", False, str(e))
else:
    print(f"{SKIP} Ollama not ready — install models first")

# T5: Single field suggestion (uses llama3.2:3b)
banner("T5 — Single Field Mapping (llama3.2:3b)")
if suggester:
    try:
        t0 = time.time()
        r = suggester.suggest_mapping("date_of_birth", "date", fhir_resource="Patient")
        el = time.time() - t0
        
        check("Field suggestion returned", True)
        check("target_path present",       "target_path" in r)
        check("confidence present",        "confidence" in r)
        check("method present",            "method" in r)
        check("status is pending_review",  r.get("status") == "pending_review")
        check("birthDate in path",         "birth" in r.get("target_path","").lower(),
              r.get("target_path"))
        check("Response time < 30s",       el < 30, f"{el:.1f}s")
        print(f"    → Suggested: {r.get('target_path')} ({r.get('confidence',0):.0%}) "
              f"[{r.get('method')}] in {el:.0f}s")
    except Exception as e:
        check("Single field mapping", False, str(e))
else:
    print(f"{SKIP} MappingSuggester not initialized")

# T6: Schema mapping with verification workflow
banner("T6 — Schema Mapping + Verification Workflow")
if suggester:
    try:
        schema = {
            "table_name": "test_patients",
            "columns": [
                {"name": "mrn",        "type": "varchar"},
                {"name": "first_name", "type": "varchar"},
                {"name": "dob",        "type": "date"},
                {"name": "sex",        "type": "char"},
            ]
        }
        
        result = suggester.suggest_schema_mapping(schema)
        
        check("Schema mapping returned",    True)
        check("4 mappings generated",       len(result["mappings"]) == 4)
        check("All status=pending_review",  
              all(m.get("status")=="pending_review" for m in result["mappings"]))
        check("accuracy_pct present",       "accuracy_pct" in result)
        check("statistics present",         "statistics" in result)
        
        # Test confirmation workflow
        confirmed = [result["mappings"][0]["source_field"]]  # approve first one only
        confirm_result = suggester.confirm_mappings(result["mappings"], confirmed)
        
        check("confirm_mappings returns saved", "saved" in confirm_result)
        check("confirm_mappings returns skipped", "skipped" in confirm_result)
        check("1 mapping saved",               len(confirm_result["saved"]) == 1)
        check("3 mappings skipped",            len(confirm_result["skipped"]) == 3)
        
        print(f"\n    Schema accuracy: {result['accuracy_pct']:.0f}%")
        print(f"    Approved: {confirm_result['saved']}")
        print(f"    Rejected: {confirm_result['skipped']}")
    except Exception as e:
        check("Schema mapping workflow", False, str(e))
else:
    print(f"{SKIP} MappingSuggester not initialized")

# T7: Chat endpoint (uses phi3)
banner("T7 — FHIR Chatbot (phi3)")
if suggester:
    try:
        print("    Asking: 'What FHIR path for patient birth date?'")
        print("    (First phi3 call may take ~60s to load model...)")
        t0 = time.time()
        answer = suggester.chat("What FHIR path should I use for a patient's birth date?")
        el = time.time() - t0
        
        check("Chat returned answer",     len(answer) > 0)
        check("Answer mentions birthDate or Patient", 
              "birthDate" in answer or "Patient" in answer,
              f"Got: {answer[:80]}...")
        print(f"    → Answer: {answer[:100]}...")
        print(f"    → Time: {el:.0f}s (phi3)")
    except Exception as e:
        check("FHIR chatbot", False, str(e))
else:
    print(f"{SKIP} MappingSuggester not initialized")

# T8: API routes (requires server running)
banner("T8 — API Endpoints")
api_up = False
try:
    import requests
    r = requests.get("http://localhost:8000/docs", timeout=3)
    api_up = r.status_code == 200
except Exception:
    pass

if api_up:
    KEY = "clk-admin-change-me-in-prod"
    HDR = {"X-API-Key": KEY}
    
    # /rag/status
    r = requests.get("http://localhost:8000/api/v1/rag/status", headers=HDR, timeout=8)
    check("GET /rag/status", r.status_code in (200,503), f"HTTP {r.status_code}")
    if r.status_code == 200:
        b = r.json()
        check("Status shows mapping_model", "mapping_model" in b)
        check("Status shows chat_model",    "chat_model" in b)
        check("mapping_model is llama3.2",  "llama3.2" in b.get("mapping_model",""))
        check("chat_model is phi3",         "phi3" in b.get("chat_model",""))
    
    # /suggest/field
    r2 = requests.post("http://localhost:8000/api/v1/rag/suggest/field", headers=HDR,
                       json={"field_name":"patient_id","field_type":"varchar",
                             "fhir_resource":"Patient"}, timeout=30)
    check("POST /suggest/field", r2.status_code in (200,503), f"HTTP {r2.status_code}")
    if r2.status_code == 200:
        s = r2.json().get("suggestion",{})
        check("Suggestion status=pending_review", s.get("status")=="pending_review")
    
    # /suggest/schema
    r3 = requests.post("http://localhost:8000/api/v1/rag/suggest/schema", headers=HDR,
                       json={"table_name":"test","columns":[{"name":"mrn","type":"varchar"}],
                             "fhir_resource":"Patient"}, timeout=30)
    check("POST /suggest/schema", r3.status_code in (200,503), f"HTTP {r3.status_code}")
    if r3.status_code == 200:
        check("Schema response has workflow field", "workflow" in r3.json())
    
    # /chat (phi3)
    r4 = requests.post("http://localhost:8000/api/v1/rag/chat", headers=HDR,
                       json={"question":"What is FHIR?"}, timeout=120)
    check("POST /chat (phi3)", r4.status_code in (200,503), f"HTTP {r4.status_code}")
else:
    print(f"  [INFO] API server not running")
    print(f"  → Start: venv\\Scripts\\uvicorn api.main:app --host 0.0.0.0 --port 8000")

# Summary
print()
print("="*64)
total  = len(results)
passed = sum(1 for _, ok in results if ok)
failed = total - passed
status = "✓ ALL PASS" if failed == 0 else f"✗ {failed} FAILED"
print(f"  RESULT: {passed}/{total} passed   [{status}]")
print()

if not ollama_ok:
    print("  Ollama not running. Start with:  ollama serve")
if ollama_ok and not models_present:
    print("  Missing models. Install with:")
    print("    ollama pull llama3.2:3b")
    print("    ollama pull phi3")
    print("    ollama pull nomic-embed-text")
if not api_up:
    print("  API server not running. Start with:")
    print("    venv\\Scripts\\uvicorn api.main:app --host 0.0.0.0 --port 8000")
print("="*64)
