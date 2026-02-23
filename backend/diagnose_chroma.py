"""Diagnose and fix the ChromaDB vector store."""
import os, sys, time
os.environ["ANONYMIZED_TELEMETRY"] = "False"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "databases", "chroma")

import chromadb, requests

# 1. Check what's in the collection
client = chromadb.PersistentClient(path=CHROMA_PATH)
col    = client.get_or_create_collection("fhir_field_mappings")
print(f"Collection count: {col.count()}")

# Peek at 2 items
sample = col.get(limit=2, include=["metadatas","embeddings","documents"])
for i, (doc, meta, emb) in enumerate(zip(sample["documents"], sample["metadatas"], sample.get("embeddings") or [None, None])):
    print(f"\nDoc {i}: {doc[:60]}")
    print(f"  target_path: {meta.get('target_path')}")
    print(f"  embedding:   {'YES dim=' + str(len(emb)) if emb else 'NONE (text-only)'}")

# 2. Test a raw query to see what distances look like
print("\n--- Raw query test ---")
try:
    # try with text first
    res = col.query(query_texts=["date of birth dob"], n_results=3, include=["metadatas","distances"])
    print("query_texts result:")
    for meta, dist in zip(res["metadatas"][0], res["distances"][0]):
        print(f"  dist={dist:.4f}  sim={1-dist:.4f}  field={meta.get('source_field')}  -> {meta.get('target_path')}")
except Exception as e:
    print(f"query_texts error: {e}")

# 3. Ollama embedding test
print("\n--- Ollama embed test ---")
OLLAMA_BASE = "http://localhost:11434"
try:
    t0 = time.time()
    r  = requests.post(f"{OLLAMA_BASE}/api/embeddings",
                       json={"model": "nomic-embed-text", "prompt": "date of birth"},
                       timeout=10)
    emb_time = round((time.time()-t0)*1000)
    if r.status_code == 200:
        v = r.json().get("embedding", [])
        print(f"OK: dim={len(v)}, latency={emb_time}ms, first5={[round(x,4) for x in v[:5]]}")
    else:
        print(f"HTTP {r.status_code}: {r.text[:100]}")
except Exception as e:
    print(f"Ollama embed failed: {e}")

# 4. Check collection distance metric
print(f"\n--- Collection metadata ---")
meta = col.metadata
print(f"  metadata: {meta}")
print(f"  (if no hnsw:space, defaults to l2)")
