"""Quick ChromaDB 1.5.x API compatibility check"""
import chromadb
print("ChromaDB version:", chromadb.__version__)
print("Has PersistentClient:", hasattr(chromadb, "PersistentClient"))
print("Has Client:", hasattr(chromadb, "Client"))

# Test PersistentClient
import tempfile, os
tmp = tempfile.mkdtemp()
try:
    client = chromadb.PersistentClient(path=tmp)
    col = client.get_or_create_collection("test_col")
    col.upsert(ids=["id1"], documents=["hello world"], metadatas=[{"key": "val"}])
    results = col.query(query_texts=["hello"], n_results=1)
    print("PersistentClient: OK")
    print("upsert + query:   OK")
    print("count:", col.count())
    client.delete_collection("test_col")
except Exception as e:
    print("PersistentClient ERROR:", e)
    import traceback; traceback.print_exc()

print("ChromaDB check DONE")
