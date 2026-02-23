"""
Rebuild ChromaDB collection with cosine distance metric.
Deletes existing L2 collection and reloads all 173 FHIR mappings.
Run time: ~6-10 minutes (nomic-embed-text is fast when warm).
"""
import os, sys, json, time, hashlib
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
import logging
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("chromadb.telemetry").setLevel(logging.CRITICAL)

sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
import requests

CHROMA_PATH  = r"C:\Projects\CareLock-Sync\databases\chroma"
MAPPINGS_JSON = r"C:\Projects\CareLock-Sync\backend\schema_mapper\fhir_mappings.json"
OLLAMA_BASE  = "http://localhost:11434"
EMBED_MODEL  = "nomic-embed-text"

def embed(text):
    """Try new then old Ollama embed endpoint."""
    try:
        r = requests.post(f"{OLLAMA_BASE}/api/embed",
                          json={"model": EMBED_MODEL, "input": text}, timeout=30)
        if r.status_code == 200:
            embs = r.json().get("embeddings", [[]])
            if embs and embs[0]: return embs[0]
    except Exception: pass
    try:
        r = requests.post(f"{OLLAMA_BASE}/api/embeddings",
                          json={"model": EMBED_MODEL, "prompt": text}, timeout=30)
        if r.status_code == 200:
            return r.json().get("embedding")
    except Exception: pass
    return None

# ── Step 1: Delete old collection ─────────────────────────────────────────────
print("Step 1: Deleting old collection (L2 metric)...")
import chromadb
client = chromadb.PersistentClient(path=CHROMA_PATH)
try:
    client.delete_collection("fhir_field_mappings")
    print("  Old collection deleted.")
except Exception as e:
    print(f"  Nothing to delete: {e}")

# ── Step 2: Create with cosine distance ───────────────────────────────────────
print("Step 2: Creating new collection with hnsw:space=cosine...")
col = client.get_or_create_collection(
    name="fhir_field_mappings",
    metadata={"description": "FHIR mapping knowledge base", "hnsw:space": "cosine"},
)
print(f"  Collection created: {col.count()} items")

# ── Step 3: Load mappings ─────────────────────────────────────────────────────
print("Step 3: Loading fhir_mappings.json...")
with open(MAPPINGS_JSON) as f:
    all_mappings = json.load(f)

resource_map = {
    "patient": "Patient", "encounter": "Encounter",
    "observation": "Observation", "medication_request": "MedicationRequest",
}
training = []
for key, fields in all_mappings.items():
    resource = resource_map.get(key, key.title())
    for fm in fields.get("field_mappings", []):
        sf = fm["source_field"]
        text_parts = [sf, sf.replace("_"," "), fm.get("data_type","string"),
                      fm["target_path"], resource]
        training.append({
            "text":          " ".join(filter(None, text_parts)),
            "source_field":  sf,
            "source_type":   fm.get("data_type","string"),
            "target_path":   fm["target_path"],
            "fhir_resource": resource,
            "confidence":    0.95,
            "transformation":str(fm.get("transformation") or "none"),
        })
print(f"  {len(training)} mappings to embed")

# ── Step 4: Embed and upsert ──────────────────────────────────────────────────
ok, failed = 0, 0
t0 = time.time()
for i, m in enumerate(training):
    emb = embed(m["text"])
    uid = hashlib.md5(m["text"].encode()).hexdigest()
    meta = {k: str(v) for k, v in m.items() if k not in ("text",)}
    try:
        if emb:
            col.upsert(documents=[m["text"]], metadatas=[meta],
                       ids=[uid], embeddings=[emb])
        else:
            col.upsert(documents=[m["text"]], metadatas=[meta], ids=[uid])
        ok += 1
    except Exception as e:
        failed += 1
    if (i+1) % 25 == 0:
        elapsed = time.time() - t0
        rate    = (i+1)/elapsed
        eta     = (len(training)-(i+1)) / rate
        print(f"  [{i+1}/{len(training)}] ok={ok} failed={failed} "
              f"elapsed={elapsed:.0f}s  ETA={eta:.0f}s")

total = time.time() - t0
print(f"\n{'='*50}")
print(f"DONE: {ok}/{len(training)} loaded, {failed} failed, {total:.1f}s")
print(f"Collection now has: {col.count()} items")

# ── Step 5: Quick sanity query ────────────────────────────────────────────────
print("\nStep 5: Sanity check — query 'patient_id integer'")
emb = embed("patient_id integer identifier")
if emb:
    res = col.query(query_embeddings=[emb], n_results=5)
    print("Top 5 similar mappings:")
    for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
        sim = round(max(0.0, 1.0 - dist/2.0), 4)
        print(f"  {meta['source_field']:<25} → {meta['target_path']:<35} sim={sim:.4f}")
else:
    print("  Embed failed — check Ollama")
