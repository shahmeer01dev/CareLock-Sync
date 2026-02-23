import sys, traceback, tempfile
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')

print("=== DIAGNOSTIC: Vector Store Seeding ===")
print()

# Step 1: Test hash embedding
from rag.vector_store import _hash_embedding
emb = _hash_embedding("date_of_birth date Patient birthDate")
print(f"Hash embedding: dim={len(emb)}, type={type(emb[0])}")

# Step 2: Test ChromaDB directly
import chromadb
tmp = tempfile.mkdtemp()
print(f"ChromaDB version: {chromadb.__version__}")
print(f"Temp dir: {tmp}")

# Step 3: Try creating a cosine collection
try:
    client = chromadb.PersistentClient(path=tmp)
    col = client.get_or_create_collection(
        "test_cosine",
        metadata={"hnsw:space": "cosine"}
    )
    print(f"Collection created OK: {col.name}")
except Exception as e:
    print(f"Collection create FAILED: {e}")
    traceback.print_exc()

# Step 4: Try upserting one item
try:
    col.upsert(
        ids=["test1"],
        embeddings=[emb],
        documents=["date_of_birth date Patient birthDate"],
        metadatas=[{
            "source_field": "date_of_birth",
            "source_type": "date",
            "target_path": "birthDate",
            "fhir_resource": "Patient",
            "transformation": "none",
            "confidence": 0.99
        }]
    )
    print(f"Upsert OK. Count: {col.count()}")
except Exception as e:
    print(f"Upsert FAILED: {e}")
    traceback.print_exc()

# Step 5: Try querying
try:
    q_emb = _hash_embedding("dob date Patient")
    res = col.query(query_embeddings=[q_emb], n_results=1)
    dist = res["distances"][0][0] if res.get("distances") else None
    sim  = max(0.0, 1.0 - dist) if dist is not None else None
    print(f"Query OK: distance={dist:.4f}, similarity={sim:.4f}")
    print(f"Result metadata: {res['metadatas'][0]}")
except Exception as e:
    print(f"Query FAILED: {e}")
    traceback.print_exc()

# Step 6: Test full MappingVectorStore
print()
print("=== Testing MappingVectorStore ===")
from rag.vector_store import MappingVectorStore
tmp2 = tempfile.mkdtemp()
try:
    vs = MappingVectorStore(persist_directory=tmp2, ollama_client=None, auto_seed=True)
    st = vs.get_statistics()
    print(f"Total mappings: {st['total_mappings']}")
    if st['total_mappings'] > 0:
        sim = vs.find_similar_mappings("date_of_birth", "date", "Patient", 3, 0.0)
        print(f"Similarity results: {sim}")
    else:
        print("PROBLEM: 0 mappings seeded!")
except Exception as e:
    print(f"MappingVectorStore FAILED: {e}")
    traceback.print_exc()

print()
print("=== DONE ===")
