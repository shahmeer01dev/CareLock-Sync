"""
Sprint 4 Setup Script - phi3 model
Installs Python dependencies, verifies Ollama, and seeds the vector store.
Run from project root:
    python scripts/setup_sprint4.py
"""
import subprocess, sys, os, time

def run(cmd, check=True):
    print(f"  > {' '.join(cmd)}")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        print(f"  ERROR: {r.stderr[:200]}")
        return False
    print("  OK")
    return True

print("=" * 60)
print("  SPRINT 4 SETUP — Ollama + ChromaDB (phi3 model)")
print("=" * 60)

# Step 1: Install/upgrade Python deps
print("\n[1] Python dependencies")
for pkg in ["chromadb", "requests"]:
    run([sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", pkg])
run([sys.executable, "-m", "pip", "uninstall", "-y", "google-generativeai"], check=False)
print("  Removed google-generativeai (replaced by Ollama)")

# Step 2: Verify Ollama
print("\n[2] Ollama verification")
import requests as req
def check_ollama():
    try:
        r = req.get("http://localhost:11434/api/tags", timeout=5)
        return [m["name"] for m in r.json().get("models", [])]
    except:
        return None

models = check_ollama()
OLLAMA_OK = False
if models is None:
    print("  !! Ollama NOT running.")
    print("  !! Download: https://ollama.com/download")
    print("  !! Start: ollama serve")
    print("  !! Model: ollama pull phi3")
else:
    print(f"  Ollama running. Models: {models}")
    OLLAMA_OK = True
    if not any("phi3" in m for m in models):
        print("  phi3 not found — pulling (~2.3 GB)...")
        subprocess.run(["ollama", "pull", "phi3"])
    if not any("nomic" in m for m in models):
        print("  Pulling nomic-embed-text (~274 MB)...")
        subprocess.run(["ollama", "pull", "nomic-embed-text"])

# Step 3: Seed ChromaDB
print("\n[3] Seeding ChromaDB vector store")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
try:
    from rag.vector_store import MappingVectorStore
    ollama_client = None
    if OLLAMA_OK:
        try:
            from rag.ollama_client import OllamaClient
            ollama_client = OllamaClient(model="phi3")
            print("  Using Ollama embeddings")
        except Exception as e:
            print(f"  Ollama client unavailable ({e}) — using hash embeddings")
    vs = MappingVectorStore(persist_directory="./databases/chroma",
                            ollama_client=ollama_client, auto_seed=True)
    stats = vs.get_statistics()
    print(f"  Vector store ready: {stats['total_mappings']} mappings")
except Exception as e:
    print(f"  ERROR: {e}")

# Step 4: Update .env
print("\n[4] Updating config/.env")
env_path = os.path.join(os.path.dirname(__file__), "..", "config", ".env")
try:
    with open(env_path) as f:
        content = f.read()
    additions = ""
    if "OLLAMA_BASE_URL" not in content:
        additions += "\n# Ollama (Sprint 4 RAG)\nOLLAMA_BASE_URL=http://localhost:11434\nOLLAMA_MODEL=phi3\n"
    if additions:
        with open(env_path, "a") as f:
            f.write(additions)
        print("  Added Ollama settings to .env")
    else:
        print("  .env already has Ollama settings")
except Exception as e:
    print(f"  Could not update .env: {e}")

# Summary
print("\n" + "=" * 60)
print("  SETUP COMPLETE")
if not OLLAMA_OK:
    print("  NEXT: Install Ollama, run: ollama serve && ollama pull phi3")
else:
    print("  NEXT:")
    print("  1. Restart API server")
    print("  2. .\\venv\\Scripts\\python scripts\\test_rag_sprint4.py")
print("=" * 60)
