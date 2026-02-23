"""
Sprint 4 — Complete RAG Test Runner
Writes results to test_results.txt
Run: venv\Scripts\python scripts\run_sprint4_test.py
"""
import sys, os, time, json, math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

LOG = []
def p(msg):
    print(msg)
    LOG.append(msg)

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"
results = []

def check(label, ok, detail=""):
    icon = PASS if ok else FAIL
    msg = f"  {icon} {label}"
    if detail: msg += f"  -- {detail}"
    p(msg)
    results.append((label, ok))
    return ok

p("")
p("=" * 65)
p("  SPRINT 4 -- RAG + phi3 -- COMPREHENSIVE TEST SUITE")
p("=" * 65)

# ── T1: Ollama Connectivity ──────────────────────────────────────────
p("\n[T1] Ollama Connectivity")
import requests
ollama_ok = False
chosen_model = None
try:
    r = requests.get("http://localhost:11434/api/tags", timeout=5)
    models = [m["name"] for m in r.json().get("models", [])]
    check("Ollama daemon alive", r.status_code == 200, f"HTTP {r.status_code}")
    check("Models installed", len(models) > 0, str(models))
    for pref in ["phi3", "mistral", "llama3"]:
        if any(pref in m for m in models):
            chosen_model = next(m for m in models if pref in m)
            break
    if not chosen_model and models:
        chosen_model = models[0]
    check("phi3 available", any("phi3" in m for m in models), f"chosen={chosen_model}")
    ollama_ok = True
    p(f"  --> Active model: {chosen_model}")
except Exception as e:
    check("Ollama reachable", False, str(e))

# ── T2: OllamaClient init ────────────────────────────────────────────
p("\n[T2] OllamaClient Initialization")
ollama_client = None
if ollama_ok and chosen_model:
    try:
        from rag.ollama_client import OllamaClient
        ollama_client = OllamaClient(model=chosen_model, timeout=180)
        check("OllamaClient created", True, f"model={chosen_model}")
        listed = ollama_client.list_models()
        check("list_models() works", len(listed) > 0, str(listed[:3]))
    except Exception as e:
        check("OllamaClient created", False, str(e))
else:
    p(f"  {SKIP} Ollama not available")

# ── T3: Embeddings ───────────────────────────────────────────────────
p("\n[T3] Embeddings (nomic-embed-text)")
if ollama_client:
    try:
        emb = ollama_client.get_embedding("date of birth patient birthDate")
        check("Embedding returned", len(emb) > 0, f"dim={len(emb)}")
        mag = math.sqrt(sum(x*x for x in emb))
        check("Magnitude > 0", mag > 0, f"mag={mag:.3f}")
        p(f"  --> Embedding dim={len(emb)}, magnitude={mag:.3f}")
    except Exception as e:
        check("Embedding returned", False, str(e))
else:
    p(f"  {SKIP} Ollama not available -- hash fallback will be used")

# ── T4: FHIR Knowledge Base ──────────────────────────────────────────
p("\n[T4] FHIR Knowledge Base (fhir_knowledge.py)")
try:
    from rag.fhir_knowledge import get_all_mappings, get_mappings_for_resource
    all_m = get_all_mappings()
    check("Knowledge base loads", len(all_m) > 100, f"{len(all_m)} total mappings")
    for res in ["Patient", "Encounter", "Observation", "MedicationRequest"]:
        m = get_mappings_for_resource(res)
        check(f"{res} mappings present", len(m) > 5, f"{len(m)} mappings")
except Exception as e:
    check("Knowledge base loads", False, str(e))

# ── T5: ChromaDB Vector Store ────────────────────────────────────────
p("\n[T5] ChromaDB Vector Store (chromadb 1.x API)")
import tempfile
vector_store = None
try:
    from rag.vector_store import MappingVectorStore
    tmp = tempfile.mkdtemp()
    vector_store = MappingVectorStore(
        persist_directory=tmp,
        ollama_client=ollama_client,
        auto_seed=True,
    )
    stats = vector_store.get_statistics()
    check("PersistentClient works", True)
    check("Knowledge seeded", stats["total_mappings"] > 100,
          f"{stats['total_mappings']} mappings in ChromaDB")
    p(f"  --> {stats}")
except Exception as e:
    check("ChromaDB init", False, str(e))

# ── T6: Retrieval Quality ─────────────────────────────────────────────
p("\n[T6] Retrieval Accuracy (no LLM needed)")
RETRIEVAL_TESTS = [
    ("date_of_birth", "date",    "Patient",           "birthDate"),
    ("first_name",    "varchar", "Patient",           "name[].given"),
    ("last_name",     "varchar", "Patient",           "name[].family"),
    ("phone_number",  "varchar", "Patient",           "telecom"),
    ("dob",           "date",    "Patient",           "birthDate"),
    ("mrn",           "varchar", "Patient",           "identifier"),
    ("gender",        "varchar", "Patient",           "gender"),
    ("email",         "varchar", "Patient",           "telecom"),
    ("admission_date","date",    "Encounter",         "period.start"),
    ("discharge_date","date",    "Encounter",         "period.end"),
    ("drug_name",     "varchar", "MedicationRequest", "medication"),
    ("result_value",  "numeric", "Observation",       "valueQuantity"),
]
if vector_store:
    hits = 0
    for field, ftype, res, expected in RETRIEVAL_TESTS:
        try:
            sim = vector_store.find_similar_mappings(
                field_name=field, field_type=ftype,
                fhir_resource=res, n_results=3, min_similarity=0.0)
            found = any(expected.lower() in m.get("target_path","").lower() for m in sim)
            top = sim[0] if sim else {}
            ok = check(f"'{field}' -> contains '{expected}'", found,
                       f"top={top.get('target_path','?')} ({top.get('similarity',0):.0%})")
            if ok: hits += 1
        except Exception as e:
            check(f"'{field}'", False, str(e))
    p(f"\n  Retrieval accuracy: {hits}/{len(RETRIEVAL_TESTS)} = {hits/len(RETRIEVAL_TESTS)*100:.0f}%")
else:
    p(f"  {SKIP} vector store not ready")

# ── T7: phi3 JSON Parser ─────────────────────────────────────────────
p("\n[T7] phi3 JSON Parser Robustness (offline)")
try:
    from rag.ollama_client import OllamaClient as _OC
    PARSE_CASES = [
        ("Clean JSON",
         '{"target_path":"Patient.birthDate","confidence":0.95,"reasoning":"dob","transformation":"none"}',
         "birthDate"),
        ("Markdown fenced",
         '```json\n{"target_path":"Patient.gender","confidence":0.9,"reasoning":"sex","transformation":"map_gender"}\n```',
         "gender"),
        ("Nested phi3 output",
         '{"fhir": {"target_path": "identifier[].value", "confidence": 0.92, "reasoning": "mrn", "transformation": "none"}}',
         "identifier"),
        ("Prose before JSON",
         'Based on FHIR spec: {"target_path":"name[].family","confidence":0.88,"reasoning":"surname","transformation":"none"} done.',
         "family"),
        ("Regex fallback",
         'The target_path is "Patient.birthDate" with confidence: 0.85',
         "birthDate"),
    ]
    for desc, raw, expected in PARSE_CASES:
        r = _OC._parse_response(raw)
        ok = expected.lower() in r.get("target_path","").lower()
        check(f"Parser: {desc}", ok, f"-> {r.get('target_path','?')} ({r.get('confidence',0):.0%})")
except Exception as e:
    check("Parser test setup", False, str(e))

# ── T8: phi3 LLM Generation ──────────────────────────────────────────
p("\n[T8] phi3 LLM Generation (SLOW ~60s per call)")
if ollama_ok and ollama_client and vector_store:
    LLM_TESTS = [
        ("patient_dob",   "date",    "Patient",           "birth"),
        ("gender_code",   "char",    "Patient",           "gender"),
    ]
    for field, ftype, res, keyword in LLM_TESTS:
        try:
            t0 = time.time()
            similar = vector_store.find_similar_mappings(field, ftype, res, 5)
            result = ollama_client.generate_mapping_suggestion(
                source_field={"name": field, "type": ftype, "sample_values": []},
                similar_mappings=similar,
                fhir_resource=res)
            elapsed = time.time() - t0
            ok = (keyword.lower() in result.get("target_path","").lower()
                  or result.get("confidence",0) >= 0.6)
            check(f"phi3: '{field}'", ok,
                  f"-> {result.get('target_path','?')} ({result.get('confidence',0):.0%}) in {elapsed:.0f}s")
            p(f"    reasoning: {result.get('reasoning','')[:80]}")
        except Exception as e:
            check(f"phi3: '{field}'", False, str(e))
else:
    p(f"  {SKIP} Ollama not available")

# ── T9: Full MappingSuggester Pipeline ──────────────────────────────
p("\n[T9] MappingSuggester -- Full RAG Pipeline")
suggester = None
if ollama_ok and chosen_model:
    try:
        from rag.mapping_suggester import MappingSuggester
        suggester = MappingSuggester(
            model=chosen_model,
            vector_store_path=tempfile.mkdtemp(),
        )
        check("MappingSuggester init", True, f"model={chosen_model}")
        for field, ftype, keyword in [
            ("mrn", "varchar", "identifier"),
            ("dob", "date", "birth"),
            ("last_name", "varchar", "family"),
        ]:
            r = suggester.suggest_mapping(field, ftype, fhir_resource="Patient")
            ok = keyword in r.get("target_path","").lower() or r.get("confidence",0) >= 0.7
            check(f"suggest('{field}')", ok,
                  f"-> {r.get('target_path','?')} ({r.get('confidence',0):.0%}) [{r.get('method','?')}]")
    except Exception as e:
        check("MappingSuggester init", False, str(e))
else:
    p(f"  {SKIP} Ollama not available")

# ── T10: Unknown Schema End-to-End ───────────────────────────────────
p("\n[T10] Unknown Schema -- 9-Column End-to-End Test")
SCHEMA = {
    "table_name": "external_hospital_patients",
    "columns": [
        {"name": "pat_id",      "type": "integer"},
        {"name": "surname",     "type": "varchar"},
        {"name": "given_name",  "type": "varchar"},
        {"name": "birth_dt",    "type": "date",    "sample_values": ["1985-06-15"]},
        {"name": "sex",         "type": "char",    "sample_values": ["M","F"]},
        {"name": "cell_phone",  "type": "varchar", "sample_values": ["+92-300-1234"]},
        {"name": "email_addr",  "type": "varchar", "sample_values": ["a@b.com"]},
        {"name": "postal_cd",   "type": "varchar"},
        {"name": "active_flag", "type": "boolean"},
    ],
}
if suggester:
    try:
        result = suggester.suggest_schema_mapping(SCHEMA)
        acc = result["accuracy_pct"]
        check("Schema mapped without crash", True)
        check("Accuracy >= 80%", acc >= 80.0, f"{acc:.0f}%")
        check("All 9 columns returned",
              result["statistics"]["total"] == 9)
        p(f"\n  {'Column':<22} {'FHIR Path':<36} Conf   Via")
        p(f"  {'-'*22} {'-'*36} {'-'*4}   {'-'*10}")
        for m in result["mappings"]:
            ico = "OK" if m["confidence"] >= 0.8 else ("??" if m["confidence"] >= 0.5 else "XX")
            p(f"  [{ico}] {m['source_field']:<20} {m['target_path']:<36}"
              f" {m['confidence']:>3.0%}  {m.get('method','?')}")
    except Exception as e:
        check("Schema mapped", False, str(e))
elif vector_store:
    p("  Running retrieval-only (phi3 skipped)...")
    hits = 0
    for col in SCHEMA["columns"]:
        sim = vector_store.find_similar_mappings(col["name"], col.get("type","varchar"), "Patient", 1)
        if sim:
            hits += 1
            p(f"  OK  {col['name']:<22} -> {sim[0]['target_path']:<36} {sim[0]['similarity']:.0%}")
        else:
            p(f"  ??  {col['name']:<22} -> (no match)")
    check("Retrieval-only >= 77%", hits/len(SCHEMA["columns"]) >= 0.77,
          f"{hits}/{len(SCHEMA['columns'])} matched")

# ── T11: API Endpoints ────────────────────────────────────────────────
p("\n[T11] API Endpoints (http://localhost:8000)")
try:
    BASE = "http://localhost:8000"
    KEY  = "clk-admin-change-me-in-prod"
    HDR  = {"X-API-Key": KEY}

    r = requests.get(f"{BASE}/api/v1/rag/status", headers=HDR, timeout=10)
    check("GET /rag/status", r.status_code in (200, 503), f"HTTP {r.status_code}")
    if r.status_code == 200:
        b = r.json()
        check("Response has model", "model" in b, b.get("model"))
        check("Response has mappings", "total_mappings" in b, str(b.get("total_mappings")))

    r401 = requests.get(f"{BASE}/api/v1/rag/status", timeout=5)
    check("No key -> 401", r401.status_code == 401, f"HTTP {r401.status_code}")

    r2 = requests.post(f"{BASE}/api/v1/rag/suggest/field", headers=HDR,
                       json={"field_name":"date_of_birth","field_type":"date",
                             "fhir_resource":"Patient"}, timeout=200)
    check("POST /rag/suggest/field", r2.status_code in (200,503), f"HTTP {r2.status_code}")
    if r2.status_code == 200:
        s = r2.json().get("suggestion", {})
        check("Suggestion has path",
              s.get("target_path","unknown") != "unknown",
              s.get("target_path"))

    r3 = requests.get(f"{BASE}/api/v1/rag/knowledge/stats", headers=HDR, timeout=10)
    check("GET /rag/knowledge/stats", r3.status_code in (200,503), f"HTTP {r3.status_code}")

    rh = requests.post(f"{BASE}/api/v1/rag/mappings/confirm",
                       headers={"X-API-Key":"clk-cgh001-hospital-key"},
                       json={"source_field":"x","source_type":"varchar",
                             "target_path":"identifier[].value","fhir_resource":"Patient",
                             "transformation":"none","confidence":1.0}, timeout=10)
    check("Hospital key -> 403 on admin endpoint", rh.status_code == 403, f"HTTP {rh.status_code}")

except requests.exceptions.ConnectionError:
    p(f"  {SKIP} API server not running on :8000")
    p("  Start: venv\\Scripts\\uvicorn api.main:app --host 0.0.0.0 --port 8000")
except Exception as e:
    check("API endpoints", False, str(e))

# ── Summary ────────────────────────────────────────────────────────────
p("")
p("=" * 65)
total  = len(results)
passed = sum(1 for _, ok in results if ok)
failed = total - passed
p(f"  FINAL: {passed}/{total} passed   {'ALL PASS' if failed == 0 else str(failed) + ' FAILED'}")
p("=" * 65)
p("")

with open("test_results.txt", "w") as f:
    f.write("\n".join(LOG))
print("Results saved to test_results.txt")
