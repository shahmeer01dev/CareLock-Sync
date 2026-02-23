"""Diagnose the Ollama embed endpoint and vector query path"""
import requests, json

BASE = "http://localhost:11434"
text = "patient_id integer identifier"

# Test old endpoint
print("=== Testing /api/embeddings (old) ===")
r = requests.post(f"{BASE}/api/embeddings", json={"model":"nomic-embed-text","prompt":text}, timeout=30)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    emb = r.json().get("embedding", [])
    print(f"Embedding dims: {len(emb)}, first3: {emb[:3]}")
else:
    print(r.text[:200])

# Test new endpoint
print("\n=== Testing /api/embed (new) ===")
r = requests.post(f"{BASE}/api/embed", json={"model":"nomic-embed-text","input":text}, timeout=30)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    d = r.json()
    emb = d.get("embeddings", [[]])[0]
    print(f"Embedding dims: {len(emb)}, first3: {emb[:3]}")
else:
    print(r.text[:200])

# Test ChromaDB query directly
print("\n=== Direct ChromaDB query (bypassing Ollama) ===")
import os, sys
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
import chromadb

client = chromadb.PersistentClient(path=r"C:\Projects\CareLock-Sync\databases\chroma")
col = client.get_collection("fhir_field_mappings")
print(f"Collection count: {col.count()}")

# Try query with text (uses default embedder)
try:
    res = col.query(query_texts=["patient_id integer"], n_results=3)
    print(f"query_texts result: {res['metadatas']}")
except Exception as e:
    print(f"query_texts FAILED: {e}")

# Try query with embedding from new endpoint
try:
    r = requests.post(f"{BASE}/api/embed", json={"model":"nomic-embed-text","input":"patient_id integer"}, timeout=30)
    if r.status_code == 200:
        emb = r.json().get("embeddings", [[]])[0]
        res = col.query(query_embeddings=[emb], n_results=3)
        print(f"query_embeddings (new endpoint) result: {[m.get('source_field') for m in res['metadatas'][0]]}")
    else:
        print(f"New endpoint failed: {r.status_code}")
except Exception as e:
    print(f"query_embeddings FAILED: {e}")
