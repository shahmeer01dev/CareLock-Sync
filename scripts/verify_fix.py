# Quick targeted test: verifies the cosine distance fix gives real similarities
# Run: .\venv\Scripts\python.exe scripts\verify_fix.py
import sys, math, time
sys.path.insert(0, r"C:\Projects\CareLock-Sync\backend")

print()
print("=" * 60)
print("  COSINE FIX VERIFICATION")
print("=" * 60)

# Step 1: nomic-embed-text via Ollama
print("\n[1] nomic-embed-text embeddings")
import requests
try:
    r = requests.post("http://localhost:11434/api/embeddings",
                      json={"model": "nomic-embed-text", "prompt": "date of birth birthDate Patient"},
                      timeout=30)
    emb1 = r.json()["embedding"]
    mag1 = math.sqrt(sum(x*x for x in emb1))
    print(f"    dim={len(emb1)}, magnitude={mag1:.2f} (raw unnormalized)")
    r2 = requests.post("http://localhost:11434/api/embeddings",
                       json={"model": "nomic-embed-text", "prompt": "dob date Patient birthDate"},
                       timeout=30)
    emb2 = r2.json()["embedding"]

    # Cosine similarity manually
    dot   = sum(a*b for a,b in zip(emb1, emb2))
    cos   = dot / (mag1 * math.sqrt(sum(x*x for x in emb2)))
    print(f"    cosine_similarity('date_of_birth', 'dob') = {cos:.4f}")
    print(f"    old formula (1-dist/2) would give: {max(0, 1-(2*(1-cos))/2):.4f} -- but only if normalized")
    print(f"    new formula (1-dist)   gives:       {max(0, 1-cos):.4f} (cosine distance)")
    print(f"    NOTE: With raw embeddings + cosine collection, dist = 1-cos, so sim = cos = {cos:.4f}")
except Exception as e:
    print(f"    ERROR: {e}")
    sys.exit(1)

# Step 2: Full vector store test with Ollama
print("\n[2] Vector store with nomic embeddings")
from rag.vector_store import MappingVectorStore
import tempfile

class OllamaEmb:
    def get_embedding(self, text):
        r = requests.post("http://localhost:11434/api/embeddings",
                          json={"model": "nomic-embed-text", "prompt": text}, timeout=30)
        return r.json()["embedding"]

oe  = OllamaEmb()
tmp = tempfile.mkdtemp()
vs  = MappingVectorStore(persist_directory=tmp, ollama_client=oe, auto_seed=True)

print(f"\n    Seeded: {vs.get_statistics()['total_mappings']} mappings")
print()
print(f"    {'Field':<22} {'Top Match':<30} {'Similarity':>10}  Status")
print(f"    {'-'*22} {'-'*30} {'-'*10}  {'-'*6}")

TEST_FIELDS = [
    ("date_of_birth", "date",    "Patient",           "birthDate"),
    ("dob",           "date",    "Patient",           "birthDate"),
    ("first_name",    "varchar", "Patient",           "name[].given[]"),
    ("last_name",     "varchar", "Patient",           "name[].family"),
    ("mrn",           "varchar", "Patient",           "identifier[].value"),
    ("gender",        "varchar", "Patient",           "gender"),
    ("phone_number",  "varchar", "Patient",           "telecom[].value"),
    ("admission_date","date",    "Encounter",         "period.start"),
    ("drug_name",     "varchar", "MedicationRequest", "medicationCodeableConcept.text"),
]

pass_count = 0
sim_sum    = 0.0
for field, ftype, resource, expected in TEST_FIELDS:
    sim = vs.find_similar_mappings(field, ftype, resource, 3, 0.0)
    top = sim[0] if sim else {}
    s   = top.get("similarity", 0.0)
    sim_sum += s
    ok  = expected in top.get("target_path", "") and s > 0.50
    status = "PASS" if ok else "FAIL"
    if ok: pass_count += 1
    print(f"    [{status}] {field:<20} {top.get('target_path','?'):<30} {s:>9.1%}  "
          + ("fast-path" if s >= 0.85 else ("ok" if s >= 0.50 else "low")))

avg = sim_sum / len(TEST_FIELDS)
print()
print(f"    Result: {pass_count}/{len(TEST_FIELDS)} correct")
print(f"    Avg similarity: {avg:.1%}  (was 0% with old L2 formula)")
print()
if avg > 0.0:
    print("  FIX CONFIRMED: cosine similarity is now giving real values")
else:
    print("  STILL BROKEN: similarity is 0% even with cosine metric")
print("=" * 60)
