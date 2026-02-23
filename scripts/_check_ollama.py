"""Quick Ollama + phi3 connectivity check"""
import requests, json, time

BASE = "http://localhost:11434"

# Check daemon
try:
    r = requests.get(f"{BASE}/api/tags", timeout=5)
    models = [m["name"] for m in r.json().get("models", [])]
    print("Ollama daemon: OK")
    print("Models installed:", models)
    phi3_ok = any("phi3" in m for m in models)
    print("phi3 available:", phi3_ok)
except Exception as e:
    print("Ollama daemon ERROR:", e)
    phi3_ok = False

if not phi3_ok:
    print("STOP: phi3 not installed. Run: ollama pull phi3")
    exit(1)

# Test generation with phi3
print("\nTesting phi3 generation (short prompt, up to 3 min for cold start)...")
t0 = time.time()
payload = {
    "model": "phi3",
    "prompt": 'Map field "dob" (date) to FHIR Patient. Reply JSON only: {"target_path":"Patient.birthDate","confidence":0.95}',
    "stream": False,
    "options": {"temperature": 0.1, "num_predict": 80}
}
r = requests.post(f"{BASE}/api/generate", json=payload, timeout=180)
elapsed = time.time() - t0
resp = r.json()
print(f"Response time: {elapsed:.1f}s")
print(f"Raw output: {resp.get('response', '')[:200]}")

# Test embedding
print("\nTesting nomic-embed-text embedding...")
r2 = requests.post(f"{BASE}/api/embeddings",
    json={"model": "nomic-embed-text", "prompt": "date_of_birth date Patient birthDate"},
    timeout=30)
if r2.status_code == 200:
    emb = r2.json().get("embedding", [])
    print(f"Embedding dim: {len(emb)}")
    mag = sum(x*x for x in emb)**0.5
    print(f"Magnitude: {mag:.4f}")
else:
    print("Embedding ERROR:", r2.status_code)

print("\nOllama check DONE")
