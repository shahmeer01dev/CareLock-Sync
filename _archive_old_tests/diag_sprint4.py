"""Sprint 4 diagnostics: reload vector store + test raw Ollama output"""
import sys, os, warnings, logging, requests, json, re
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)
sys.path.insert(0, r"C:\Projects\CareLock-Sync\backend")
os.chdir(r"C:\Projects\CareLock-Sync\backend")

# ── Step 1: Force-reload all 41 mappings ─────────────────────────────────────
from rag.vector_store import MappingVectorStore
vs = MappingVectorStore(persist_directory=r"C:\Projects\CareLock-Sync\databases\chroma")
print(f"Before reload: {vs.count()} mappings")
loaded = vs.load_all_fhir_mappings()
print(f"After  reload: {vs.count()} mappings")

# ── Step 2: Test similarity search works ──────────────────────────────────────
similar = vs.find_similar_mappings("patient_id", "integer", n_results=3)
print(f"\nSimilarity search 'patient_id': {len(similar)} results")
for m in similar:
    print(f"  {m.get('source_field')} -> {m.get('target_path')}  sim={m.get('similarity')}")

# ── Step 3: Test raw Ollama — does it actually return valid JSON? ──────────────
print("\nTesting raw Ollama (llama3.2:3b)...")
prompt = (
    "You are a FHIR mapping expert. Map this field.\n"
    "Field: patient_id  Type: integer  Samples: 1,2,3\n"
    "Output ONLY valid JSON like this example:\n"
    '{"target_path":"Patient.id","confidence":0.95,"reasoning":"Primary key","transformation":"to_string"}\n'
    "JSON:"
)
r = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama3.2:3b", "prompt": prompt, "stream": False,
          "options": {"temperature": 0.1, "num_predict": 150}},
    timeout=60,
)
raw = r.json().get("response", "")
print(f"Raw response ({len(raw)} chars):")
print(repr(raw[:400]))

# Try parsing it
cleaned = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()
match = re.search(r"\{[^{}]*\}", cleaned, re.DOTALL)
if match:
    try:
        parsed = json.loads(match.group())
        print(f"\nParsed OK: target_path={parsed.get('target_path')}  conf={parsed.get('confidence')}")
    except Exception as e:
        print(f"\nParse FAILED: {e}")
        print("Matched block:", match.group())
else:
    print("\nNo JSON block found in response")
