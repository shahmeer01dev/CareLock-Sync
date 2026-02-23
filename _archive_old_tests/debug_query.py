import sys
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
import requests, chromadb

path = r'C:\Projects\CareLock-Sync\databases\chroma'
client = chromadb.PersistentClient(path=path)
col = client.get_or_create_collection("fhir_field_mappings")
print(f"Count: {col.count()}")

# Get embedding for test query
def embed(text):
    r = requests.post('http://localhost:11434/api/embeddings',
        json={'model': 'nomic-embed-text', 'prompt': text}, timeout=15)
    return r.json()['embedding']

query = "date_of_birth date"
emb = embed(query)
print(f"Query embedding dim: {len(emb)}")

# Query ChromaDB directly
result = col.query(query_embeddings=[emb], n_results=5)
print(f"\nQuery results for '{query}':")
for doc, meta, dist in zip(result['documents'][0], result['metadatas'][0], result['distances'][0]):
    sim = round(1.0 - dist, 4)
    print(f"  {meta['source_field']} -> {meta['target_path']} | dist={dist:.4f} | sim={sim:.4f}")

# Test with sim threshold = 0 (accept all)
print("\n--- All results (no threshold) ---")
for meta, dist in zip(result['metadatas'][0], result['distances'][0]):
    print(f"  {meta['source_field']} -> {meta['target_path']} | dist={round(dist,4)}")
