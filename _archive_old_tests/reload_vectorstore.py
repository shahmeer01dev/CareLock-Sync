"""
Reload ChromaDB vector store — run this once after Ollama restart.
Clears the stale 31-mapping store and re-embeds all 173 FHIR mappings.
"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ['ANONYMIZED_TELEMETRY'] = 'False'

import chromadb
import requests

OLLAMA_BASE   = "http://localhost:11434"
EMBED_MODEL   = "nomic-embed-text:latest"
CHROMA_PATH   = "./databases/chroma"
MAPPINGS_FILE = "./backend/schema_mapper/fhir_mappings.json"

def embed(text: str):
    r = requests.post(f"{OLLAMA_BASE}/api/embeddings",
                      json={"model": EMBED_MODEL, "prompt": text}, timeout=30)
    return r.json().get("embedding")

print("=== ChromaDB Reload ===")

# 1. Connect and wipe the old collection
client = chromadb.PersistentClient(path=CHROMA_PATH)
try:
    client.delete_collection("fhir_field_mappings")
    print("Cleared old collection")
except:
    pass
col = client.create_collection("fhir_field_mappings",
                                metadata={"description": "FHIR mapping knowledge base"})

# 2. Load all 173 mappings from JSON
with open(MAPPINGS_FILE) as f:
    all_mappings = json.load(f)

resource_map = {
    "patient":            "Patient",
    "encounter":          "Encounter",
    "observation":        "Observation",
    "medication_request": "MedicationRequest",
}

training = []
for resource_key, data in all_mappings.items():
    fhir_resource = resource_map.get(resource_key, resource_key.title())
    for fm in data.get("field_mappings", []):
        training.append({
            "source_field":   fm["source_field"],
            "source_type":    fm.get("data_type", "string"),
            "target_path":    fm["target_path"],
            "fhir_resource":  fhir_resource,
            "confidence":     0.95,
            "transformation": fm.get("transformation") or "none",
        })

print(f"Loaded {len(training)} mappings from JSON")

# 3. Embed and upsert in batches
import hashlib
ok = 0
fail = 0
t0 = time.time()

for i, m in enumerate(training):
    field   = m["source_field"]
    text    = f"{field} {field.replace('_',' ')} {m['source_type']} {m['target_path']} {m['fhir_resource']}"
    uid     = hashlib.md5(text.encode()).hexdigest()
    meta    = {k: str(v) for k, v in m.items()}
    meta["confidence"] = float(m["confidence"])

    try:
        emb = embed(text)
        if emb:
            col.upsert(documents=[text], metadatas=[meta], ids=[uid], embeddings=[emb])
        else:
            col.upsert(documents=[text], metadatas=[meta], ids=[uid])
        ok += 1
        if (i+1) % 20 == 0:
            elapsed = time.time() - t0
            rate = (i+1) / elapsed
            eta  = (len(training) - i - 1) / rate
            print(f"  [{i+1}/{len(training)}] {ok} loaded  ETA: {eta:.0f}s")
    except Exception as e:
        fail += 1
        print(f"  FAIL [{field}]: {e}")

elapsed = time.time() - t0
print(f"\nDone: {ok} loaded, {fail} failed in {elapsed:.1f}s")
print(f"ChromaDB now has {col.count()} mappings")
