import sys, os, time, math
sys.path.insert(0, r"C:\Projects\CareLock-Sync\backend")

results = {"pass": 0, "fail": 0}
def check(label, ok, detail=""):
    icon = "PASS" if ok else "FAIL"
    print(f"  [{icon}] {label}" + (f"  ({detail})" if detail else ""))
    results["pass" if ok else "fail"] += 1

print("\n" + "="*60)
print("  SPRINT 4 RAG TESTS")
print("="*60)

# T1: Imports
print("\n[T1] Module Imports")
mods_ok = {}
for mod in ["rag.ollama_client", "rag.fhir_knowledge", "rag.vector_store", "rag.mapping_suggester"]:
    try:
        __import__(mod)
        check(f"import {mod}", True)
        mods_ok[mod] = True
    except Exception as e:
        check(f"import {mod}", False, str(e)[:80])
        mods_ok[mod] = False

# T2: FHIR Knowledge
print("\n[T2] FHIR Knowledge Base")
try:
    from rag.fhir_knowledge import get_all_mappings, get_mappings_for_resource
    m = get_all_mappings()
    check("Total > 100 mappings", len(m) > 100, f"{len(m)}")
    for r in ["Patient","Encounter","Observation","MedicationRequest"]:
        rm = get_mappings_for_resource(r)
        check(f"  {r}", len(rm) > 0, f"{len(rm)} entries")
except Exception as e:
    check("FHIR Knowledge", False, str(e))

# T3: Parser (offline)
print("\n[T3] phi3 JSON Parser (offline)")
from rag.ollama_client import OllamaClient
p = OllamaClient._parse_response
CASES = [
    ('{"target_path":"Patient.birthDate","confidence":0.95,"reasoning":"dob","transformation":"none"}', 'birthDate'),
    ('```json\n{"target_path":"Patient.gender","confidence":0.9,"reasoning":"sex","transformation":"map_gender"}\n```', 'gender'),
    ('Sure! {"fhir":{"target_path":"identifier[].value","confidence":0.92,"reasoning":"mrn","transformation":"none"}}', 'identifier'),
    ('text then {"target_path":"name[].family","confidence":0.88,"reasoning":"surname","transformation":"none"} end', 'family'),
    ('target_path: Patient.birthDate\nconfidence: 0.85', 'birthDate'),
]
for raw, exp in CASES:
    r = p(raw)
    ok = exp in r.get("target_path","")
    check(f"  parse: expect '{exp}'", ok, f"got={r['target_path']!r}")

# T4: Ollama connectivity
print("\n[T4] Ollama + phi3")
import requests as req
ollama_ok = False
client = None
try:
    r = req.get("http://localhost:11434/api/tags", timeout=5)
    models = [m["name"] for m in r.json().get("models", [])]
    check("Daemon reachable", True, str(models))
    check("phi3 installed", any("phi3" in m for m in models))
    check("nomic-embed-text installed", any("nomic" in m for m in models))
    ollama_ok = any("phi3" in m for m in models)
    if ollama_ok:
        from rag.ollama_client import OllamaClient
        client = OllamaClient(model="phi3", timeout=180)
        check("OllamaClient init", True)
        emb = client.get_embedding("date_of_birth patient birthDate")
        check("Embedding dim > 100", len(emb) > 100, f"dim={len(emb)}")
except Exception as e:
    check("Ollama connectivity", False, str(e)[:80])

# T5: ChromaDB
print("\n[T5] ChromaDB Vector Store")
import tempfile
vs = None
try:
    from rag.vector_store import MappingVectorStore
    tmp = tempfile.mkdtemp()
    vs = MappingVectorStore(persist_directory=tmp, ollama_client=client, auto_seed=True)
    stats = vs.get_statistics()
    check("ChromaDB init", True)
    check("Auto-seeded > 100 mappings", stats["total_mappings"] > 100, f"{stats['total_mappings']}")
except Exception as e:
    check("ChromaDB", False, str(e)[:80])

# T6: Retrieval
print("\n[T6] Similarity Retrieval")
TESTS = [
    ("date_of_birth","date","Patient","birthDate"),
    ("first_name","varchar","Patient","given"),
    ("last_name","varchar","Patient","family"),
    ("phone_number","varchar","Patient","telecom"),
    ("mrn","varchar","Patient","identifier"),
    ("gender","char","Patient","gender"),
    ("admission_date","date","Encounter","period"),
    ("drug_name","varchar","MedicationRequest","medication"),
    ("result_value","numeric","Observation","valueQuantity"),
]
if vs:
    hits = 0
    for field, ftype, resource, kw in TESTS:
        res = vs.find_similar_mappings(field, ftype, resource, n_results=3, min_similarity=0.0)
        found = any(kw.lower() in m.get("target_path","").lower() for m in res)
        if found: hits += 1
        top = res[0] if res else {}
        check(f"  '{field}' contains '{kw}'", found,
              f"top={top.get('target_path','?')} {top.get('similarity',0):.0%}")
    check(f"Retrieval >= 80%", hits/len(TESTS) >= 0.8, f"{hits}/{len(TESTS)}")

# T7: LLM generation (slow)
print("\n[T7] phi3 LLM Mapping (each ~60s, please wait)")
if client and vs:
    for field, ftype, resource, kw in [
        ("patient_dob","date","Patient","birth"),
        ("gender_code","char","Patient","gender"),
    ]:
        t0 = time.time()
        sim = vs.find_similar_mappings(field, ftype, resource, 5)
        r = client.generate_mapping_suggestion({"name":field,"type":ftype}, sim, resource)
        elapsed = time.time()-t0
        ok = kw in r.get("target_path","").lower() or r.get("confidence",0) >= 0.65
        check(f"  phi3 maps '{field}'", ok,
              f"-> {r.get('target_path','?')} ({r.get('confidence',0):.0%}) in {elapsed:.0f}s")
else:
    print("  [SKIP] Ollama not available")

# T8: Full pipeline
print("\n[T8] Full MappingSuggester Pipeline")
if ollama_ok:
    try:
        from rag.mapping_suggester import MappingSuggester
        sg = MappingSuggester(model="phi3", vector_store_path=tempfile.mkdtemp())
        check("MappingSuggester init", True)
        schema = {"table_name":"test","fhir_resource":"Patient","columns":[
            {"name":"pat_id","type":"integer"},{"name":"surname","type":"varchar"},
            {"name":"birth_dt","type":"date"},{"name":"sex","type":"char"},
            {"name":"cell_phone","type":"varchar"},{"name":"postal_cd","type":"varchar"},
        ]}
        result = sg.suggest_schema_mapping(schema)
        acc = result["accuracy_pct"]
        check("Schema mapped", True)
        check(f"Accuracy >= 75%", acc >= 75.0, f"{acc:.0f}%")
        print(f"\n  {'Column':<18} {'FHIR Path':<36} {'Conf':>5}  Method")
        print(f"  {'-'*18} {'-'*36} {'-'*5}  {'-'*10}")
        for m in result["mappings"]:
            ic = "HI" if m["confidence"]>=0.8 else ("MED" if m["confidence"]>=0.5 else "LOW")
            print(f"  [{ic}] {m['source_field']:<16} {m['target_path']:<36} {m['confidence']:>4.0%}  {m.get('method','?')}")
    except Exception as e:
        check("MappingSuggester", False, str(e)[:80])
else:
    print("  [SKIP] Ollama not available")

print()
print("="*60)
total = results["pass"] + results["fail"]
print(f"  RESULT: {results['pass']}/{total} passed  {'ALL PASS' if results['fail']==0 else str(results['fail'])+' FAILED'}")
print("="*60)
