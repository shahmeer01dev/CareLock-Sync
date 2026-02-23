import os, sys
os.environ["ANONYMIZED_TELEMETRY"] = "False"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rag.vector_store import MappingVectorStore

CHROMA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "databases", "chroma")
vs = MappingVectorStore(persist_directory=CHROMA)
print(f"Total in store: {vs.count()}")

tests = [
    ("dob",           "date",    "birthDate"),
    ("fname",         "string",  "name[0].given[0]"),
    ("mrn",           "string",  "identifier[0].value"),
    ("sex",           "string",  "gender"),
    ("admission_dt",  "string",  "period.start"),
    ("los",           "integer", "length.value"),
    ("loinc_code",    "string",  "code.coding[0].code"),
    ("drug_name",     "string",  "medicationCodeableConcept.text"),
    ("sig",           "string",  "dosageInstruction[0].timing.code.text"),
]
correct = 0
for field, dtype, expected in tests:
    results = vs.find_similar_mappings(field, dtype, n_results=3)
    best = results[0] if results else {}
    got  = best.get("target_path", "NONE")
    hit  = "PASS" if got == expected else "FAIL"
    if got == expected:
        correct += 1
    sim = best.get("similarity", 0)
    print(f"  [{hit}] {field:20s} -> {got:50s} sim={sim:.3f}")

print(f"\nRetrieval accuracy: {correct}/{len(tests)} = {correct*100//len(tests)}%")
