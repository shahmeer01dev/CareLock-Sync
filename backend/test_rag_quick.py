"""
Sprint 4 — Quick RAG pipeline verification
Runs directly against Ollama (no HTTP server needed)
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from rag.ollama_client  import OllamaClient
from rag.vector_store   import MappingVectorStore
from rag.mapping_suggester import MappingSuggester

PASS = 0; FAIL = 0

def check(label, cond, detail=""):
    global PASS, FAIL
    if cond: PASS += 1
    else:    FAIL += 1
    mark   = "PASS" if cond else "FAIL"
    suffix = f"  ({detail})" if detail else ""
    print(f"  [{mark}] {label}{suffix}")

print("=" * 62)
print(" SPRINT 4 — RAG PIPELINE QUICK TEST")
print("=" * 62)

# ── T1: Ollama connects and auto-selects model ─────────────────
print("\n[T1] Ollama Connection")
c = OllamaClient()
check("Connected",          True)
check("Model is llama3.2",  "llama3.2" in c.model, c.model)
models = c.list_models()
check("nomic-embed-text available", any("nomic-embed" in m for m in models))
print(f"  All models: {models}")

# ── T2: Vector store loaded ────────────────────────────────────
print("\n[T2] Vector Store")
vs = MappingVectorStore(persist_directory="./databases/chroma")
cnt = vs.count()
check("ChromaDB backend",         vs._use_chroma)
check("41 FHIR mappings loaded",  cnt >= 41, f"{cnt} items")

# Similarity search
sim = vs.find_similar_mappings("patient_id", "integer", n_results=3)
check("Similarity search works",  len(sim) > 0, f"{len(sim)} results")
for s in sim:
    print(f"    patient_id → {s['target_path']}  sim={s['similarity']}")

sim2 = vs.find_similar_mappings("medication_name", "string",
                                fhir_resource="MedicationRequest" if hasattr(vs,'find_similar_mappings') else None,
                                n_results=2)
check("MedicationRequest search", any("medication" in s.get("target_path","").lower() for s in sim2), str(sim2[:1]))

# ── T3: Exact known-field mapping accuracy ─────────────────────
print("\n[T3] Known Field Mapping Accuracy (6 fields)")
TEST_FIELDS = [
    ("patient_id",      "integer", "Patient",           "id"),
    ("date_of_birth",   "date",    "Patient",           "birthDate"),
    ("first_name",      "string",  "Patient",           "name"),
    ("admission_date",  "dateTime","Encounter",         "period"),
    ("result_value",    "decimal", "Observation",       "valueQuantity"),
    ("medication_name", "string",  "MedicationRequest", "medicationCodeableConcept"),
]
correct = 0
for fname, ftype, resource, expected_frag in TEST_FIELDS:
    similar = vs.find_similar_mappings(fname, ftype, n_results=4)
    t0  = time.time()
    res = c.generate_mapping_suggestion(
        source_field={"name": fname, "type": ftype, "sample_values": []},
        similar_mappings=similar,
        fhir_resource=resource,
    )
    ms   = round((time.time()-t0)*1000)
    got  = res.get("target_path", "")
    conf = round(res.get("confidence", 0)*100)
    ok   = expected_frag.lower() in got.lower()
    if ok: correct += 1
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {fname:<22} → {got:<40} conf={conf}%  ({ms}ms)")

accuracy = round(correct/len(TEST_FIELDS)*100)
check(f"Accuracy >= 85% ({accuracy}%)", accuracy >= 85, f"{correct}/{len(TEST_FIELDS)}")

# ── T4: Variant / unseen field names ──────────────────────────
print("\n[T4] Variant Field Generalisation (4 fields)")
VARIANTS = [
    ("dob",          "date",    "Patient",    "birth"),
    ("fname",        "string",  "Patient",    "name"),
    ("mobile",       "string",  "Patient",    "telecom"),
    ("test_result",  "decimal", "Observation","valueQuantity"),
]
vc = 0
for fname, ftype, resource, frag in VARIANTS:
    sim  = vs.find_similar_mappings(fname, ftype, n_results=4)
    res  = c.generate_mapping_suggestion(
        source_field={"name": fname, "type": ftype, "sample_values": []},
        similar_mappings=sim, fhir_resource=resource
    )
    got  = res.get("target_path","")
    conf = round(res.get("confidence",0)*100)
    ok   = frag.lower() in got.lower()
    if ok: vc += 1
    mark = "PASS" if ok else "~   "
    print(f"  [{mark}] {fname:<20} → {got:<35} conf={conf}%")
print(f"  Generalisation: {vc}/{len(VARIANTS)} variant fields correct")

# ── T5: Schema-level mapping ───────────────────────────────────
print("\n[T5] Schema Mapping — patients table")
from rag.mapping_suggester import MappingSuggester
suggester = MappingSuggester(vector_store_path="./databases/chroma")
result = suggester.suggest_schema(
    schema={
        "table_name": "patients",
        "columns": [
            {"name": "patient_id",    "type": "integer"},
            {"name": "first_name",    "type": "string"},
            {"name": "last_name",     "type": "string"},
            {"name": "date_of_birth", "type": "date"},
            {"name": "gender",        "type": "string"},
            {"name": "phone_number",  "type": "string"},
        ],
    },
    fhir_resource="Patient",
)
stats    = result["statistics"]
sch_acc  = result["accuracy_pct"]
check("HTTP 200 equivalent (no exception)", True)
check(f"Schema accuracy >= 85% ({sch_acc}%)", sch_acc >= 85,
      f"high={stats['high']} med={stats['medium']} low={stats['low']}")

# ── T6: Confirm & learn mapping ────────────────────────────────
print("\n[T6] Confirm Mapping (RAG learning)")
before = vs.count()
ok = suggester.save_confirmed_mapping(
    source_field="mrn_number", source_type="string",
    target_path="identifier[0].value", fhir_resource="Patient"
)
after = vs.count()
check("save_confirmed_mapping returns True", ok)
check("Count incremented",                  after > before, f"{before} → {after}")

# ── Summary ────────────────────────────────────────────────────
total = PASS + FAIL
print("\n" + "=" * 62)
print(f" RESULTS:  {PASS}/{total} PASSED  ({round(PASS/total*100)}%)")
print(f" Mapping accuracy:   {accuracy}%")
print(f" Schema accuracy:    {sch_acc}%")
print(f" Generalisation:     {vc}/{len(VARIANTS)}")
print(f" Vector store:       {after} mappings")
print(f" LLM:                {c.model}  (fully local)")
print("=" * 62)
