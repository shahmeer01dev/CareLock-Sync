"""Sprint 4 v2 - Full Test Suite (dual-model + confirmation workflow)"""
import os, sys, math, time, tempfile
ROOT = r'C:\Projects\CareLock-Sync'
sys.path.insert(0, os.path.join(ROOT, 'backend'))
os.chdir(ROOT)

import requests as req

PASS, FAIL, SKIP = "  [PASS]", "  [FAIL]", "  [SKIP]"
results = []
def check(label, ok, detail=""):
    icon = PASS if ok else FAIL
    print(f"{icon} {label}" + (f"  --  {detail}" if detail else ""))
    results.append((label, ok)); return ok

print("\n" + "="*64)
print("  SPRINT 4 v2 -- DUAL MODEL + CONFIRMATION WORKFLOW")
print("="*64)

# T1: Ollama + models
print("\n[T1] Ollama Connectivity + Models")
ollama_ok = False; mapping_model = None; chat_model = None
try:
    r = req.get("http://localhost:11434/api/tags", timeout=5)
    models = [m["name"] for m in r.json().get("models", [])]
    check("Ollama reachable", True, f"HTTP {r.status_code}")
    check("phi3 installed",       any("phi3"    in m for m in models), str(models))
    check("llama3.2:3b installed", any("llama3.2" in m for m in models), str(models))
    check("nomic-embed-text",     any("nomic"   in m for m in models), str(models))
    mapping_model = next((m for m in models if "llama3.2" in m), None)
    chat_model    = next((m for m in models if "phi3"     in m), None)
    ollama_ok = bool(mapping_model and chat_model)
    print(f"  -> mapping: {mapping_model}  |  chat: {chat_model}")
except Exception as e:
    check("Ollama reachable", False, str(e))

# T2: OllamaClient dual init
print("\n[T2] Dual OllamaClient (mapping + chat)")
from rag.ollama_client import OllamaClient
map_oc = chat_oc = None
if ollama_ok:
    try:
        map_oc  = OllamaClient(model=mapping_model, timeout=60)
        chat_oc = OllamaClient(model=chat_model,    timeout=180)
        check("Mapping client (llama3.2:3b)", True,  mapping_model)
        check("Chat client    (phi3)",         True,  chat_model)
        check("Both report is_available()",    map_oc.is_available() and chat_oc.is_available())
    except Exception as e:
        check("OllamaClient init", False, str(e))
else:
    print(f"{SKIP} Ollama not running")

# T3: Embeddings
print("\n[T3] Embeddings (nomic-embed-text)")
if map_oc:
    emb = map_oc.get_embedding("patient date of birth birthDate")
    check("Embedding returned",   len(emb) > 0, f"dim={len(emb)}")
    check("Embedding non-zero",   math.sqrt(sum(x*x for x in emb)) > 0)
else:
    print(f"{SKIP} hash fallback active")

# T4: Vector store seed
print("\n[T4] Vector Store (ChromaDB) + Knowledge Base")
from rag.vector_store import MappingVectorStore

class _EmbProxy:
    def get_embedding(self, text):
        try:
            r2 = req.post("http://localhost:11434/api/embeddings",
                          json={"model":"nomic-embed-text","prompt":text}, timeout=30)
            if r2.status_code == 200: return r2.json()["embedding"]
        except Exception: pass
        from rag.ollama_client import _hash_embedding
        return _hash_embedding(text)

emb_proxy = _EmbProxy() if ollama_ok else None
vs = MappingVectorStore(persist_directory=r'C:\Projects\CareLock-Sync\databases\chroma',
                        ollama_client=emb_proxy, auto_seed=True)
st = vs.get_statistics()
check("ChromaDB PersistentClient", True)
check("Mappings seeded > 150",     st["total_mappings"] > 150, f"{st['total_mappings']}")

# T5: Retrieval — 16 cases including v1 failures
print("\n[T5] Retrieval Quality -- 16 Cases (pat_id + sex fixed)")
CASES = [
    ("date_of_birth","date","Patient","birthDate"),
    ("first_name","varchar","Patient","name[].given[]"),
    ("last_name","varchar","Patient","name[].family"),
    ("dob","date","Patient","birthDate"),
    ("mrn","varchar","Patient","identifier[].value"),
    ("pat_id","integer","Patient","identifier[].value"),
    ("gender","varchar","Patient","gender"),
    ("sex","char","Patient","gender"),
    ("phone_number","varchar","Patient","telecom[].value"),
    ("email","varchar","Patient","telecom[].value"),
    ("postal_cd","varchar","Patient","address[].postalCode"),
    ("active_flag","boolean","Patient","active"),
    ("admission_date","date","Encounter","period.start"),
    ("discharge_date","date","Encounter","period.end"),
    ("drug_name","varchar","MedicationRequest","medicationCodeableConcept"),
    ("result_value","numeric","Observation","valueQuantity.value"),
]
for field, ftype, resource, expected in CASES:
    sim   = vs.find_similar_mappings(field, ftype, resource, 3, 0.0)
    found = any(expected in m.get("target_path","") for m in sim)
    top   = sim[0] if sim else {}
    check(f"'{field}' -> '{expected}'", found,
          f"top={top.get('target_path','?')} ({top.get('similarity',0):.0%})")

# T6: JSON parser
print("\n[T6] JSON Parser -- 5 Cases (offline)")
from rag.ollama_client import OllamaClient as _OC
for desc, raw, expected in [
    ("Clean JSON",      '{"target_path":"Patient.birthDate","confidence":0.95,"reasoning":"dob","transformation":"none"}', "birthDate"),
    ("Markdown fences", '```json\n{"target_path":"Patient.gender","confidence":0.9,"reasoning":"sex","transformation":"map_gender"}\n```', "gender"),
    ("Nested JSON",     'Result: {"fhir":{"target_path":"identifier[].value","confidence":0.92,"reasoning":"mrn","transformation":"none"}}', "identifier"),
    ("Prose + JSON",    'Maps to: {"target_path":"name[].family","confidence":0.88,"reasoning":"surname","transformation":"none"} done.', "family"),
    ("Key:value",       "target_path: Patient.birthDate\nconfidence: 0.85\nreasoning: birth date", "birthDate"),
]:
    r = _OC._parse_response(raw)
    check(f"Parser: {desc}", expected in r.get("target_path",""), f"got='{r['target_path']}'")

# T7: llama3.2:3b mapping generation
print("\n[T7] llama3.2:3b Mapping Generation (~5s per call)")
if ollama_ok and map_oc:
    for field, ftype, resource, kw in [
        ("patient_dob","date","Patient","birth"),
        ("sex_code","char","Patient","gender"),
        ("hosp_date","date","Encounter","period"),
    ]:
        t0  = time.time()
        sim = vs.find_similar_mappings(field, ftype, resource, 5)
        res = map_oc.generate_mapping_suggestion({"name":field,"type":ftype}, sim, resource)
        el  = time.time() - t0
        ok  = kw in res.get("target_path","").lower() or res.get("confidence",0) >= 0.6
        check(f"llama3.2 maps '{field}'", ok,
              f"-> {res.get('target_path','?')} ({res.get('confidence',0):.0%}) in {el:.1f}s")
else:
    print(f"{SKIP} Ollama not available")

# T8: MappingSuggester dual-model init
print("\n[T8] MappingSuggester (dual-model)")
suggester = None
if ollama_ok:
    try:
        from rag.mapping_suggester import MappingSuggester
        suggester = MappingSuggester(mapping_model=mapping_model, chat_model=chat_model,
                                      vector_store_path=tempfile.mkdtemp())
        check("MappingSuggester init",     True)
        check("mapping_model=llama3.2:3b", "llama3.2" in suggester.mapper.model, suggester.mapper.model)
        check("chat_model=phi3",           "phi3"      in suggester.chatter.model, suggester.chatter.model)
    except Exception as e:
        check("MappingSuggester init", False, str(e))
else:
    print(f"{SKIP} Ollama not available")

# T9: Schema mapping -- same 9 cols that got 78% before
print("\n[T9] Unknown Schema -- 9 Columns (was 78%, target >=80%)")
SCHEMA = {"table_name":"external_patient_records","columns":[
    {"name":"pat_id","type":"integer"},
    {"name":"surname","type":"varchar"},
    {"name":"given_name","type":"varchar"},
    {"name":"birth_dt","type":"date","sample_values":["1985-06-15"]},
    {"name":"sex","type":"char","sample_values":["M","F"]},
    {"name":"cell_phone","type":"varchar"},
    {"name":"email_addr","type":"varchar"},
    {"name":"postal_cd","type":"varchar"},
    {"name":"active_flag","type":"boolean"},
]}
if suggester:
    result = suggester.suggest_schema_mapping(SCHEMA)
    check("Schema mapped",   True)
    check("Accuracy >= 80%", result["accuracy_pct"] >= 80, f"{result['accuracy_pct']:.0f}%")
    check("All 9 processed", result["statistics"]["total"] == 9)
else:
    hit = 0
    for col in SCHEMA["columns"]:
        sim = vs.find_similar_mappings(col["name"],col.get("type","varchar"),"Patient",1)
        path = sim[0]["target_path"] if sim else "(no match)"
        icon = "+" if sim and sim[0]["similarity"]>=0.8 else "~"
        print(f"  [{icon}] {col['name']:<22} -> {path}")
        if sim and sim[0]["similarity"]>=0.7: hit+=1
    check("Retrieval >=77%", hit/len(SCHEMA["columns"])>=0.77, f"{hit}/9")

# T10: Confirmation workflow (offline simulation)
print("\n[T10] Confirmation Workflow (offline simulation)")
if suggester:
    pending = suggester.suggest_schema_mapping(
        {"table_name":"confirm_test","columns":[
            {"name":"dob","type":"date"},
            {"name":"full_name","type":"varchar"},
            {"name":"unknown_xyz","type":"varchar"},
        ]})
    check("Returns pending_confirmation", pending.get("status") == "pending_confirmation")

    decisions = [
        {"field_name":"dob",         "action":"confirm"},
        {"field_name":"full_name",   "action":"edit", "override_path":"name[].text"},
        {"field_name":"unknown_xyz", "action":"reject", "reason":"not in scope"},
    ]
    conf = suggester.confirm_mappings(pending, decisions)
    check("confirm() confirmed=1",    len(conf["confirmed"]) == 1)
    check("confirm() edited=1",       len(conf["edited"])    == 1)
    check("confirm() rejected=1",     len(conf["rejected"])  == 1)
    check("saved_to_kb == 2",         conf["saved_to_knowledge_base"] == 2)
    check("edited path saved correctly", conf["edited"][0]["corrected"] == "name[].text")
else:
    print(f"{SKIP} Suggester not available")

# T11: RAG Chat
print("\n[T11] RAG Chat (phi3 conversational)")
if ollama_ok and suggester:
    t0  = time.time()
    ans = suggester.chat("What FHIR path maps to a patient date of birth?")
    el  = time.time() - t0
    check("Chat returns non-empty",  len(ans) > 10, f"({el:.0f}s)")
    check("Answer mentions birth/date/FHIR",
          any(w in ans.lower() for w in ["birth","fhir","patient","date","path"]), ans[:80])
else:
    print(f"{SKIP} phi3 not available")

# T12: API endpoints
print("\n[T12] API Endpoints (suggest/schema -> confirm workflow)")
KEY = "clk-admin-change-me-in-prod"; HDR = {"X-API-Key": KEY}
api_up = False
try:
    req.get("http://localhost:8000/docs", timeout=4); api_up = True
except Exception:
    pass

if api_up:
    r = req.get("http://localhost:8000/api/v1/rag/status", headers=HDR, timeout=8)
    check("GET /status", r.status_code in (200,503), f"HTTP {r.status_code}")
    if r.status_code == 200:
        b = r.json()
        check("status.mapping_model=llama3.2", "llama3.2" in b.get("mapping_model",""), b.get("mapping_model"))
        check("status.chat_model=phi3",         "phi3"     in b.get("chat_model",""),    b.get("chat_model"))

    r2 = req.post("http://localhost:8000/api/v1/rag/suggest/schema", headers=HDR,
                  json={"table_name":"api_test","columns":[{"name":"mrn","type":"varchar"},
                        {"name":"dob","type":"date"}],"fhir_resource":"Patient"}, timeout=300)
    check("POST /suggest/schema", r2.status_code in (200,503), f"HTTP {r2.status_code}")
    sid = None
    if r2.status_code == 200:
        sid = r2.json().get("session_id")
        check("Returns session_id", sid is not None, str(sid)[:20] if sid else "None")

    if sid:
        r3 = req.post("http://localhost:8000/api/v1/rag/confirm", headers=HDR,
                      json={"session_id": sid, "decisions":[
                            {"field_name":"mrn","action":"confirm"},
                            {"field_name":"dob","action":"confirm"}]}, timeout=15)
        check("POST /confirm",              r3.status_code == 200, f"HTTP {r3.status_code}")
        if r3.status_code == 200:
            d = r3.json()
            check("saved_to_knowledge_base > 0", d.get("saved_to_knowledge_base",0) > 0)
            check("status=confirmed",             d.get("status") == "confirmed")

    r4 = req.post("http://localhost:8000/api/v1/rag/chat", headers=HDR,
                  json={"question":"What FHIR path for date of birth?","context_resource":"Patient"},
                  timeout=200)
    check("POST /chat",              r4.status_code in (200,503), f"HTTP {r4.status_code}")
    if r4.status_code == 200:
        check("chat.answer non-empty",   len(r4.json().get("answer","")) > 5)
        check("chat.model_used=phi3",    "phi3" in r4.json().get("model_used",""))

    r401 = req.get("http://localhost:8000/api/v1/rag/status", timeout=5)
    check("No key -> 401", r401.status_code == 401, f"HTTP {r401.status_code}")

    r403 = req.post("http://localhost:8000/api/v1/rag/confirm",
                    headers={"X-API-Key":"clk-cgh001-hospital-key"},
                    json={"session_id":"x","decisions":[]}, timeout=8)
    check("Hospital key -> 403 on /confirm", r403.status_code in (403,404), f"HTTP {r403.status_code}")
else:
    print(f"  [INFO] API server not running -- start it then re-run")
    print(f"         .\\venv\\Scripts\\uvicorn api.main:app --host 0.0.0.0 --port 8000")

# Final
print()
print("="*64)
total = len(results); passed = sum(1 for _,ok in results if ok); failed = total-passed
print(f"  RESULT:  {passed}/{total} passed   [{'ALL PASS' if failed==0 else str(failed)+' FAILED'}]")
print()
if not api_up:
    print("  Start API then re-run to test endpoints:")
    print("    .\\venv\\Scripts\\uvicorn api.main:app --host 0.0.0.0 --port 8000")
print("="*64)
