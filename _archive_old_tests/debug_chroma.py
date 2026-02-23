import sys
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')

# Check what's actually in ChromaDB
import chromadb, os

path = r'C:\Projects\CareLock-Sync\databases\chroma'
client = chromadb.PersistentClient(path=path)
col = client.get_or_create_collection("fhir_field_mappings")
print(f"Total in collection: {col.count()}")

if col.count() > 0:
    # Peek at a few
    results = col.peek(5)
    print("Sample documents:", results['documents'][:3])
    print("Sample metadata:", results['metadatas'][:2])
    
    # Check if embeddings are stored
    ids = results['ids']
    got = col.get(ids=ids[:2], include=['embeddings', 'documents', 'metadatas'])
    has_embed = got['embeddings'] is not None and len(got['embeddings'][0]) > 0 if got['embeddings'] else False
    print(f"Has embeddings stored: {has_embed}")
    if has_embed:
        print(f"Embedding dim: {len(got['embeddings'][0])}")

# Test Ollama embedding directly
import requests
r = requests.post('http://localhost:11434/api/embeddings',
    json={'model': 'nomic-embed-text', 'prompt': 'date_of_birth date field'}, timeout=15)
print(f"\nOllama embed test: status={r.status_code}")
if r.status_code == 200:
    emb = r.json().get('embedding', [])
    print(f"Embedding dim: {len(emb)}, first5: {emb[:5]}")
