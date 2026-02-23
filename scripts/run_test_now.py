"""Sprint 4 RAG -- Comprehensive Live Test (ASCII-only, Windows cp1252-safe)"""
import sys, os, time, json, math, requests, tempfile, struct, hashlib
sys.path.insert(0, r"C:\Projects\CareLock-Sync\backend")
# Force UTF-8 on Windows stdout to avoid charmap errors
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

P = []; F = []
def ok(label, detail=""):
    print("  [PASS] " + label + (("  -- " + str(detail)) if detail else ""))
    P.append(label)
def fail(label, detail=""):
    print("  [FAIL] " + label + (("  -- " + str(detail)) if detail else ""))
    F.append(label)
def chk(label, cond, detail=""):
    (ok if cond else fail)(label, str(detail) if detail else "")
    return cond

print()
print("=" * 68)
print("  SPRINT 4 -- RAG + phi3 + ChromaDB LIVE TEST")
print("=" * 68)

# ==========================================================================
# [1] OLLAMA CONNECTIVITY
# ==========================================================================
print("\n[1] Ollama Connectivity")
ollama_ok = False; ACTIVE_MODEL = None
try:
    r = requests.get("http://localhost:11434/api/tags", timeout=5)
    models = [m["name"] for m in r.json().get("models", [])]
    chk("Ollama daemon reachable", r.status_code == 200)
    chk("Models installed",        len(models) > 0, models)
    chk("phi3 present",            any("phi3"  in m for m in models), models)
    chk("nomic-embed-text present",any("nomic" in m for m in models), models)
    ACTIVE_MODEL = next((m for m in models if "phi3" in m), models[0] if models else None)
    ollama_ok = True
    print("  Active model: " + str(ACTIVE_MODEL))
except Exception as e:
    fail("Ollama daemon reachable", str(e))

# ==========================================================================
# [2] OLLAMA CLIENT MODULE
# ==========================================================================
print("\n[2] OllamaClient Module")
client = None
try:
    from rag.ollama_client import OllamaClient, _hash_embedding
    if ollama_ok and ACTIVE_MODEL:
        client = OllamaClient(model=ACTIVE_MODEL, timeout=180)
        ok("OllamaClient init", "model=" + ACTIVE_MODEL)
        ml = client.list_models()
        chk("list_models()", len(ml) > 0, ml)
    else:
        fail("OllamaClient init", "Ollama not running")
except Exception as e:
    fail("OllamaClient import/init", str(e))

# ==========================================================================
# [3] JSON PARSER ROBUSTNESS (offline, instant)
# ==========================================================================
print("\n[3] phi3 JSON Parser Robustness (offline, no LLM needed)")
try:
    from rag.ollama_client import OllamaClient as _OC
    CASES = [
        ("Clean JSON",
         '{"target_path":"Patient.birthDate","confidence":0.95,"reasoning":"dob","transformation":"none"}',
         "birthDate"),
        ("Markdown fences",
         '```json\n{"target_path":"Patient.gender","confidence":0.9,"reasoning":"sex","transformation":"map_gender"}\n```',
         "gender"),
        ("phi3 nested verbose",
         'Based on FHIR: {"fhir":{"target_path":"identifier[].value","confidence":0.92,"reasoning":"mrn","transformation":"none"}}',
         "identifier"),
        ("Prose then JSON",
         'The mapping:\n{"target_path":"name[].family","confidence":0.88,"reasoning":"surname","transformation":"none"}',
         "family"),
        ("key:value fallback",
         'target_path: Patient.birthDate\nconfidence: 0.85',
         "birthDate"),
    ]
    for desc, raw, expected in CASES:
        r = _OC._parse_response(raw)
        chk("Parser: " + desc,
            expected in r.get("target_path",""),
            r.get("target_path","?") + " (" + str(round(r.get("confidence",0)*100)) + "%)")
except Exception as e:
    fail("Parser tests", str(e))
