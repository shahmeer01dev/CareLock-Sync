"""
Sprint 4 — Pre-load FHIR mapping knowledge base into ChromaDB.
Run ONCE before starting the API server.
Uses: ollama nomic-embed-text for embeddings (local, no API key).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print(" CareLock Sync — Sprint 4 Vector Store Preloader")
print("=" * 60)

# 1. Verify Ollama is up
import requests
try:
    r = requests.get("http://localhost:11434/api/tags", timeout=5)
    models = [m["name"] for m in r.json().get("models", [])]
    print(f"\n[OK] Ollama running — models: {', '.join(models)}")
except Exception as e:
    print(f"\n[FAIL] Ollama not running: {e}")
    print("  Start it with: ollama serve")
    sys.exit(1)

# 2. Init vector store
from rag.vector_store import MappingVectorStore
chroma_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "databases", "chroma")
print(f"\n[INFO] ChromaDB path: {chroma_path}")

store = MappingVectorStore(persist_directory=chroma_path)
before = store.count()
print(f"[INFO] Current mappings in store: {before}")

if before >= 41:
    print(f"[OK] Store already has {before} mappings — skipping preload")
    print("     Delete the chroma directory to force reload")
else:
    print("\n[LOAD] Loading all 4 FHIR resource mappings...")
    loaded = store.load_all_fhir_mappings()
    after  = store.count()
    print(f"\n[OK] Preload complete: {loaded} added, {after} total in store")

# 3. Quick smoke test
print("\n[TEST] Smoke test — find_similar_mappings('patient_id')")
results = store.find_similar_mappings("patient_id", "integer", n_results=3)
for r in results:
    print(f"  {r.get('source_field','?'):<25} -> {r.get('target_path','?'):<35}  sim={r.get('similarity',0):.3f}")

print("\n[TEST] find_similar_mappings('date_of_birth')")
results = store.find_similar_mappings("date_of_birth", "date", n_results=3)
for r in results:
    print(f"  {r.get('source_field','?'):<25} -> {r.get('target_path','?'):<35}  sim={r.get('similarity',0):.3f}")

print(f"\n[DONE] Vector store ready — {store.count()} FHIR mappings indexed")
print("       You can now start the API: uvicorn api.main:app ...")
print("=" * 60)
