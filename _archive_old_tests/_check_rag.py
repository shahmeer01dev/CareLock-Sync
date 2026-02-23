import sys, os
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
os.chdir(r'C:\Projects\CareLock-Sync\backend')
from rag.vector_store import MappingVectorStore
from rag.ollama_client import OllamaClient

# Vector store state
vs = MappingVectorStore('./databases/chroma')
stats = vs.get_stats()
print(f"ChromaDB backend: {stats['backend']}")
print(f"Mappings cached:  {stats['total_mappings']}")

# Ollama state
print(f"Ollama available: {OllamaClient.is_available()}")
c = OllamaClient()
print(f"Active model:     {c.model}")
print(f"All models:       {c.list_models()}")
