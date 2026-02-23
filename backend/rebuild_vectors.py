"""
rebuild_vectors.py — Sprint 4
Clears ChromaDB and reloads from the expanded fhir_mappings.json.
Run after any change to fhir_mappings.json or after generate_fhir_mappings.py.
Requires: API server to be STOPPED (or it holds the ChromaDB lock).
"""
import os, sys, time, json
os.environ["ANONYMIZED_TELEMETRY"] = "False"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "databases", "chroma")
JSON_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema_mapper", "fhir_mappings.json")

print("=" * 60)
print("CareLock Sync — Vector Store Rebuild")
print("=" * 60)

# 1. Count what's in JSON
with open(JSON_PATH) as f:
    data = json.load(f)
total_mappings = sum(len(v["field_mappings"]) for v in data.values())
print(f"\nSource: {JSON_PATH}")
print(f"Mappings in JSON: {total_mappings}")
for k, v in data.items():
    print(f"  {k:22s}: {len(v['field_mappings'])}")

# 2. Wipe old collection
print(f"\nWiping ChromaDB at: {CHROMA_PATH}")
try:
    import chromadb
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        client.delete_collection("fhir_field_mappings")
        print("  Deleted collection 'fhir_field_mappings'")
    except Exception:
        print("  Collection didn't exist yet (fresh start)")
except Exception as e:
    print(f"  ChromaDB init warning: {e}")

# 3. Reload
print("\nReloading with embeddings...")
from rag.vector_store import MappingVectorStore
vs = MappingVectorStore(persist_directory=CHROMA_PATH)

t0    = time.time()
count = vs.load_all_fhir_mappings()
elapsed = round(time.time() - t0, 1)

print(f"\n✓ Loaded {count}/{total_mappings} mappings in {elapsed}s")
print(f"  Backend: {vs.get_stats()['backend']}")
print(f"  Total in store: {vs.count()}")

# 4. Smoke tests
print("\nSmoke tests:")
tests = [
    ("dob",       "date",    "Patient"),
    ("fname",     "string",  "Patient"),
    ("mrn",       "string",  "Patient"),
    ("sex",       "string",  "Patient"),
    ("admit_dt",  "string",  "Encounter"),
    ("los",       "integer", "Encounter"),
    ("loinc_code","string",  "Observation"),
    ("drug_name", "string",  "MedicationRequest"),
    ("sig",       "string",  "MedicationRequest"),
]
correct, total_tests = 0, len(tests)
EXPECTED = {
    "dob": "birthDate", "fname": "name[0].given[0]", "mrn": "identifier[0].value",
    "sex": "gender",    "admit_dt": "period.start",   "los": "length.value",
    "loinc_code": "code.coding[0].code",
    "drug_name": "medicationCodeableConcept.text",    "sig": "dosageInstruction[0].timing.code.text",
}
for field, dtype, resource in tests:
    results = vs.find_similar_mappings(field, dtype, n_results=3)
    best = results[0] if results else {}
    got  = best.get("target_path", "?")
    exp  = EXPECTED.get(field, "?")
    hit  = "✓" if got == exp else "✗"
    if got == exp: correct += 1
    print(f"  {hit} {field:18s} -> {got:48s} (sim={best.get('similarity', 0):.3f})")

print(f"\nRetrieval accuracy: {correct}/{total_tests} = {correct/total_tests:.0%}")
print("=" * 60)
print("Done. Restart the API server.")
