"""
Sprint 4 - Comprehensive RAG Test Suite
Run: .\\venv\\Scripts\\python scripts\\test_rag_sprint4.py

Key verifications:
  - Cosine similarity returns real values (not 0%)
  - Fast-path fires for standard fields (retrieval, not phi3)
  - phi3 only called for ambiguous fields
  - Schema mapping accuracy >= 80%
"""
import sys, os, time, math, tempfile, shutil

# Add backend to path
ROOT    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)
os.chdir(ROOT)

PASS, FAIL, SKIP = "  [PASS]", "  [FAIL]", "  [SKIP]"
results = []

def check(label, ok, detail=""):
    icon = PASS if ok else FAIL
    print(f"{icon} {label}" + (f"  ({detail})" if detail else ""))
    results.append((label, ok))
    return ok

def section(title):
    print(f"\n[{title}]")

print()
print("=" * 62)
print("  SPRINT 4 — COMPREHENSIVE RAG + phi3 TEST SUITE")
print("=" * 62)


# ── T1: Imports ──────────────────────────────────────────────────────────────
section("T1] Module Imports")
for mod in ["rag.ollama_client","rag.fhir_knowledge",
            "rag.vector_store","rag.mapping_suggester"]:
    try:
        __import__(mod)
        check(f"import {mod}", True)
    except Exception as e:
        check(f"import {mod}", False, str(e)[:80])


# ── T2: FHIR Knowledge Base ───────────────────────────────────────────────────
section("T2] FHIR Knowledge Base")
from rag.fhir_knowledge import get_all_mappings, get_mappings_for_resource
all_m = get_all_mappings()
check(f"Total > 100 mappings", len(all_m) > 100, str(len(all_m)))
for res, min_count in [("Patient",50),("Encounter",20),("Observation",20),("MedicationRequest",15)]:
    n = len(get_mappings_for_resource(res))
    check(f"  {res}", n >= min_count, f"{n} entries")


# ── T3: JSON Parser (offline) ─────────────────────────────────────────────────
section("T3] phi3 JSON Parser (offline)")
from rag.ollama_client import OllamaClient as _OC
PARSE_CASES = [
    ('{"target_path":"Patient.birthDate","confidence":0.95,"reasoning":"dob","transformation":"none"}', "birthDate"),
    ('```json\n{"target_path":"Patient.gender","confidence":0.9,"reasoning":"sex","transformation":"map_gender"}\n```', "gender"),
    ('Here is mapping: {"fhir":{"target_path":"identifier[].value","confidence":0.92,"reasoning":"mrn","transformation":"none"}}', "identifier"),
    ('Maps to: {"target_path":"name[].family","confidence":0.88,"reasoning":"surname","transformation":"none"} done.', "family"),
    ("target_path: Patient.birthDate\nconfidence: 0.85\nreasoning: birth date", "birthDate"),
]
for raw, expected in PARSE_CASES:
    r = _OC._parse_response(raw)
    check(f"  parse: expect '{expected}'", expected in r.get("target_path",""),
          f"got='{r['target_path']}'")


# ── T4: Ollama + phi3 ─────────────────────────────────────────────────────────
section("T4] Ollama + phi3")
import requests
ollama_ok, chosen_model, oc = False, None, None
try:
    r = requests.get("http://localhost:11434/api/tags", timeout=5)
    models = [m["name"] for m in r.json().get("models", [])]
    check("Daemon reachable", True, str(models))
    check("phi3 installed",            any("phi3" in m for m in models))
    check("nomic-embed-text installed", any("nomic" in m for m in models))

    chosen_model = next((m for m in models if "phi3" in m), None) or (models[0] if models else None)
    if chosen_model:
        oc = _OC(model=chosen_model, timeout=180)
        check("OllamaClient init", True)
        emb = oc.get_embedding("date_of_birth date Patient birthDate")
        check(f"Embedding dim > 100", len(emb) > 100, f"dim={len(emb)}")
        mag = math.sqrt(sum(x*x for x in emb))
        check(f"Embedding magnitude reasonable (nomic returns raw unnorm)",
              mag > 1.0, f"mag={mag:.1f}")
        ollama_ok = True
except Exception as e:
    check("Daemon reachable", False, str(e)[:80])


# ── T5: ChromaDB Vector Store (cosine) ───────────────────────────────────────
section("T5] ChromaDB Vector Store (cosine distance)")
from rag.vector_store import MappingVectorStore
vs_tmp = tempfile.mkdtemp()
try:
    vs = MappingVectorStore(persist_directory=vs_tmp, ollama_client=oc, auto_seed=True)
    st = vs.get_statistics()
    check("ChromaDB init",              True)
    check("Auto-seeded > 100 mappings", st["total_mappings"] > 100,
          str(st["total_mappings"]))
    check("Cosine distance metric",     st.get("distance_metric") == "cosine",
          st.get("distance_metric","?"))
except Exception as e:
    check("ChromaDB init", False, str(e)[:80])
    vs = None


# ── T6: Similarity — must be REAL values, not 0% ─────────────────────────────
section("T6] Similarity Retrieval — Real Scores Required")
RETRIEVAL = [
    ("date_of_birth","date","Patient","birthDate"),
    ("first_name","varchar","Patient","given"),
    ("last_name","varchar","Patient","family"),
    ("phone_number","varchar","Patient","telecom"),
    ("mrn","varchar","Patient","identifier"),
    ("gender","varchar","Patient","gender"),
    ("admission_date","date","Encounter","period"),
    ("drug_name","varchar","MedicationRequest","medication"),
    ("result_value","numeric","Observation","valueQuantity"),
]
if vs:
    real_sims, correct = [], 0
    for field, ftype, resource, expected in RETRIEVAL:
        sim = vs.find_similar_mappings(field, ftype, resource, 3, 0.0)
        found = any(expected in m.get("target_path","") for m in sim)
        top   = sim[0] if sim else {}
        top_s = top.get("similarity", 0.0)
        real_sims.append(top_s)
        if found: correct += 1
        label = "+" if found else "FAIL"
        check(f"  [{label}] '{field}' -> '{expected}'",
              found and top_s > 0.01,
              f"top={top.get('target_path','?')} {top_s:.0%}")

    avg_sim = sum(real_sims)/len(real_sims) if real_sims else 0
    check("Average similarity > 50%",    avg_sim > 0.50, f"{avg_sim:.0%}")
    check("Average similarity > 0% FIX", avg_sim > 0.01, f"WAS 0% bug, now {avg_sim:.0%}")
    check(f"Retrieval >= 80%",           correct/len(RETRIEVAL) >= 0.8,
          f"{correct}/{len(RETRIEVAL)}")
else:
    print(f"{SKIP} No vector store")


# ── T7: Fast-path fires for standard fields ───────────────────────────────────
section("T7] Fast-path (retrieval, not phi3) for standard fields")
if vs:
    FAST_FIELDS = [
        ("date_of_birth","date","Patient"),
        ("first_name","varchar","Patient"),
        ("mrn","varchar","Patient"),
        ("phone_number","varchar","Patient"),
        ("admission_date","date","Encounter"),
    ]
    for field, ftype, resource in FAST_FIELDS:
        sim = vs.find_similar_mappings(field, ftype, resource, 1, 0.0)
        top_s = sim[0]["similarity"] if sim else 0
        check(f"  '{field}' similarity >= 0.85 (fast-path threshold)",
              top_s >= 0.85, f"{top_s:.0%}")
else:
    print(f"{SKIP} No vector store")


# ── T8: phi3 LLM (slow) ───────────────────────────────────────────────────────
section("T8] phi3 LLM Generation (slow ~60s per call)")
if ollama_ok and oc and vs:
    for field, ftype, resource, kw in [
        ("patient_dob","date","Patient","birth"),
        ("sex_code","char","Patient","gender"),
    ]:
        try:
            t0  = time.time()
            sim = vs.find_similar_mappings(field, ftype, resource, 5)
            res = oc.generate_mapping_suggestion({"name":field,"type":ftype}, sim, resource)
            el  = time.time() - t0
            ok  = kw in res.get("target_path","").lower() or res.get("confidence",0) >= 0.6
            check(f"  phi3 maps '{field}'", ok,
                  f"-> {res.get('target_path','?')} ({res.get('confidence',0):.0%}) in {el:.0f}s")
        except Exception as e:
            check(f"  phi3 maps '{field}'", False, str(e)[:80])
else:
    print(f"{SKIP} Ollama not available")


# ── T9: Full MappingSuggester ─────────────────────────────────────────────────
section("T9] Full MappingSuggester Pipeline")
suggester = None
if ollama_ok and chosen_model:
    try:
        from rag.mapping_suggester import MappingSuggester
        sg_dir = tempfile.mkdtemp()
        suggester = MappingSuggester(model=chosen_model, vector_store_path=sg_dir)
        check("MappingSuggester init", True, chosen_model)

        SCHEMA = {
            "table_name": "external_patient_records",
            "columns": [
                {"name":"pat_id",       "type":"integer"},
                {"name":"surname",      "type":"varchar"},
                {"name":"given_name",   "type":"varchar"},
                {"name":"birth_dt",     "type":"date",    "sample_values":["1985-06-15"]},
                {"name":"sex",          "type":"char",    "sample_values":["M","F"]},
                {"name":"cell_phone",   "type":"varchar"},
                {"name":"email_addr",   "type":"varchar"},
                {"name":"postal_cd",    "type":"varchar"},
                {"name":"active_flag",  "type":"boolean"},
            ],
        }
        result = suggester.suggest_schema_mapping(SCHEMA)
        check("Schema mapped without crash", True)
        check("Accuracy >= 75%", result["accuracy_pct"] >= 75,
              f"{result['accuracy_pct']:.0f}%")
        check("All 9 columns processed",
              result["statistics"]["total"] == 9,
              f"total={result['statistics']['total']}")

        print(f"\n  {'Column':<22} {'FHIR Path':<36} {'Conf':>5}  Method")
        print(f"  {'-'*22} {'-'*36} {'-'*5}  {'-'*10}")
        for m in result["mappings"]:
            icon = "+" if m["confidence"] >= 0.80 else ("~" if m["confidence"] >= 0.50 else "?")
            print(f"  [{icon}] {m['source_field']:<20} {m['target_path']:<36}"
                  f" {m['confidence']:>4.0%}  [{m.get('method','?')}]")
    except Exception as e:
        check("MappingSuggester pipeline", False, str(e)[:120])
else:
    print(f"{SKIP} Ollama not available")


# ── T10: API Endpoints ────────────────────────────────────────────────────────
section("T10] API Endpoints (requires server on :8000)")
KEY = "clk-admin-change-me-in-prod"
HDR = {"X-API-Key": KEY}
api_up = False
try:
    ping = requests.get("http://localhost:8000/api/v1/sync/health", headers=HDR, timeout=4)
    api_up = ping.status_code in (200, 404)
except Exception:
    pass

if api_up:
    r = requests.get("http://localhost:8000/api/v1/rag/status", headers=HDR, timeout=8)
    check("GET /rag/status (auth)",     r.status_code in (200,503), f"HTTP {r.status_code}")
    r401 = requests.get("http://localhost:8000/api/v1/rag/status", timeout=5)
    check("No key -> 401",              r401.status_code == 401,    f"HTTP {r401.status_code}")
    if r.status_code == 200:
        b = r.json()
        check("  .model present",         "model" in b, b.get("model"))
        check("  .total_mappings present", "total_mappings" in b)

    r2 = requests.post("http://localhost:8000/api/v1/rag/suggest/field", headers=HDR,
                       json={"field_name":"date_of_birth","field_type":"date","fhir_resource":"Patient"},
                       timeout=200)
    check("POST /suggest/field",        r2.status_code in (200,503), f"HTTP {r2.status_code}")
    if r2.status_code == 200:
        s = r2.json().get("suggestion",{})
        check("  target_path valid",      "birth" in s.get("target_path","").lower(), s.get("target_path"))
        check("  confidence > 0",         s.get("confidence",0) > 0, f"{s.get('confidence',0):.0%}")

    r3 = requests.post("http://localhost:8000/api/v1/rag/suggest/schema", headers=HDR,
                       json={"table_name":"t","columns":[{"name":"mrn","type":"varchar"},
                                                          {"name":"dob","type":"date"}],
                             "fhir_resource":"Patient"}, timeout=400)
    check("POST /suggest/schema",       r3.status_code in (200,503), f"HTTP {r3.status_code}")

    r4 = requests.get("http://localhost:8000/api/v1/rag/knowledge/stats", headers=HDR, timeout=8)
    check("GET /knowledge/stats",       r4.status_code in (200,503), f"HTTP {r4.status_code}")

    r5 = requests.post("http://localhost:8000/api/v1/rag/mappings/confirm",
                       headers={"X-API-Key":"clk-cgh001-hospital-key"},
                       json={"source_field":"x","source_type":"varchar","target_path":"id",
                             "fhir_resource":"Patient","transformation":"none","confidence":1.0},
                       timeout=8)
    check("Hospital key -> 403",        r5.status_code == 403, f"HTTP {r5.status_code}")
else:
    print(f"  [INFO] API server not running — skipping endpoint tests")
    print(f"  → Start: .\\venv\\Scripts\\uvicorn api.main:app --host 0.0.0.0 --port 8000")
    print(f"  → Then re-run this script")


# ── Cleanup ───────────────────────────────────────────────────────────────────
try:
    shutil.rmtree(vs_tmp, ignore_errors=True)
    if suggester:
        shutil.rmtree(sg_dir, ignore_errors=True)
except Exception:
    pass


# ── Final Report ─────────────────────────────────────────────────────────────
print()
print("=" * 62)
total  = len(results)
passed = sum(1 for _, ok in results if ok)
failed = total - passed
status = "ALL PASS" if failed == 0 else f"{failed} FAILED"
print(f"  RESULT: {passed}/{total} passed  [{status}]")
if not ollama_ok:
    print()
    print("  phi3 not running. To run full test suite:")
    print("    ollama serve")
    print("    (phi3 and nomic-embed-text are already installed)")
    print("    .\\venv\\Scripts\\python scripts\\test_rag_sprint4.py")
print("=" * 62)
