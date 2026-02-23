"""Direct ChromaDB and embedding diagnostic."""
import sys, os
os.environ["ANONYMIZED_TELEMETRY"] = "False"
sys.path.insert(0, r"C:\Projects\CareLock-Sync\backend")

from rag.vector_store import MappingVectorStore, _ollama_embed

vs = MappingVectorStore(persist_directory=r"C:\Projects\CareLock-Sync\databases\chroma")
print(f"Store count : {vs.count()}")
print(f"Backend     : {vs.get_stats()}")

# Test embedding
emb = _ollama_embed("patient_id integer")
print(f"Embedding OK: {emb is not None}, dim: {len(emb) if emb else 0}")
if emb:
    print(f"First 3 vals: {emb[:3]}")

# Raw ChromaDB query with embedding
if emb:
    res = vs._col.query(query_embeddings=[emb], n_results=5)
    metas = res["metadatas"][0]
    dists = res["distances"][0]
    print(f"\nRaw ChromaDB query (embedding):")
    for m, d in zip(metas, dists):
        sim = max(0.0, 1.0 - d / 2.0)
        print(f"  sim={sim:.4f} dist={d:.4f}  {m.get('source_field')} -> {m.get('target_path')}")

# Raw query with text only (fallback path)
res2 = vs._col.query(query_texts=["patient_id integer"], n_results=5)
print(f"\nRaw ChromaDB query (text only):")
for m, d in zip(res2["metadatas"][0], res2["distances"][0]):
    sim = max(0.0, 1.0 - d / 2.0)
    print(f"  sim={sim:.4f} dist={d:.4f}  {m.get('source_field')} -> {m.get('target_path')}")

# find_similar_mappings
results = vs.find_similar_mappings("patient_id", "integer", n_results=5, min_similarity=0.0)
print(f"\nfind_similar_mappings: {len(results)} results")
for r in results:
    print(f"  {r.get('source_field')} -> {r.get('target_path')} sim={r.get('similarity')}")

# Test with date_of_birth
results2 = vs.find_similar_mappings("date_of_birth", "date", n_results=3, min_similarity=0.0)
print(f"\ndate_of_birth: {len(results2)} results")
for r in results2:
    print(f"  {r.get('source_field')} -> {r.get('target_path')} sim={r.get('similarity')}")
