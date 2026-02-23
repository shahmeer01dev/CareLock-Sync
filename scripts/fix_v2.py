"""Fix fhir_knowledge.py and .env for dual-model v2."""
import re, os

ROOT = r"C:\Projects\CareLock-Sync"
os.chdir(ROOT)

# ── Fix fhir_knowledge.py ──────────────────────────────────────────────────
path = os.path.join(ROOT, "backend", "rag", "fhir_knowledge.py")
with open(path, "r", encoding="utf-8") as f:
    src = f.read()

# Add pat_id aliases to identifier mapping
if "pat_id" not in src:
    src = src.replace(
        '"aliases": "mrn patient_id record_number national_id pid patientid id"',
        '"aliases": "mrn patient_id record_number national_id pid patientid id pat_id pat_num subject_id patid"'
    )
    print("Added pat_id to identifier aliases")
else:
    print("pat_id already in aliases")

# Add dedicated sex entry
sex_entry = '''    {"source_field": "sex", "source_type": "char", "target_path": "gender",
     "fhir_resource": "Patient", "transformation": "map_gender", "confidence": 0.99,
     "aliases": "sex_code gender_code patient_sex f_m m_f sex_at_birth gendercode sexcode sex_cd gender_cd"},
'''
if '"source_field": "sex"' not in src:
    # Insert after the gender line
    marker = '{"source_field":"gender"'
    pos = src.find(marker)
    if pos == -1:
        # try alternate format
        marker = '"source_field": "gender"'
        pos = src.find(marker)
    if pos != -1:
        end = src.find("\n", pos) + 1
        src = src[:end] + sex_entry + src[end:]
        print("Added dedicated sex/gender entry")
    else:
        # Append before FHIR_TRAINING_MAPPINGS closing bracket
        src = src.replace(
            "]\n\ndef get_all_mappings",
            "    # sex field (alias for gender)\n" + sex_entry + "]\n\ndef get_all_mappings"
        )
        print("Appended sex entry at end of mappings list")
else:
    print("sex entry already present")

with open(path, "w", encoding="utf-8") as f:
    f.write(src)
print("fhir_knowledge.py saved")

# ── Update .env ────────────────────────────────────────────────────────────
env_path = os.path.join(ROOT, "config", ".env")
with open(env_path, "r", encoding="utf-8") as f:
    env = f.read()

adds = []
if "MAPPING_MODEL" not in env:
    adds.append("MAPPING_MODEL=llama3.2:3b")
if "CHAT_MODEL" not in env:
    adds.append("CHAT_MODEL=phi3")

if adds:
    with open(env_path, "a", encoding="utf-8") as f:
        f.write("\n# Dual-model RAG v2\n" + "\n".join(adds) + "\n")
    print("Added to .env:", adds)
else:
    print(".env already has MAPPING_MODEL and CHAT_MODEL")

# ── Wipe and reseed ChromaDB ────────────────────────────────────────────────
import shutil, sys, importlib
sys.path.insert(0, os.path.join(ROOT, "backend"))

chroma_path = os.path.join(ROOT, "databases", "chroma")
if os.path.exists(chroma_path):
    shutil.rmtree(chroma_path)
    print("Wiped old ChromaDB")
os.makedirs(chroma_path, exist_ok=True)

import requests as req
ollama_embed = None
try:
    r = req.get("http://localhost:11434/api/tags", timeout=5)
    models = [m["name"] for m in r.json().get("models", [])]
    if any("nomic" in m for m in models):
        class _Emb:
            def get_embedding(self, text):
                try:
                    r2 = req.post("http://localhost:11434/api/embeddings",
                                  json={"model": "nomic-embed-text", "prompt": text}, timeout=30)
                    if r2.status_code == 200:
                        return r2.json()["embedding"]
                except Exception:
                    pass
                from rag.ollama_client import _hash_embedding
                return _hash_embedding(text)
        ollama_embed = _Emb()
        print("Using nomic-embed-text for embeddings")
    else:
        print("Using hash embeddings (nomic not found)")
except Exception as e:
    print(f"Using hash embeddings (Ollama: {e})")

from rag.vector_store import MappingVectorStore
vs = MappingVectorStore(persist_directory=chroma_path,
                        ollama_client=ollama_embed, auto_seed=True)
n = vs.get_statistics()["total_mappings"]
print(f"ChromaDB seeded: {n} mappings")
print("\nAll fixes applied successfully.")
