"""
demo_rag.py — Sprint 4 RAG Demo
CareLock Sync: Ollama-powered FHIR field mapping + clinical Q&A

Scenarios:
  1. RAG System Status   (Ollama + vector store health)
  2. Single Field Mapping (RAG retrieval + LLM generation)
  3. Full Schema Mapping  (map entire unknown hospital table)
  4. Human Confirmation   (learning loop)
  5. Clinical Q&A Chat    (grounded on live FHIR data)

Usage:
    python demo/demo_rag.py
"""
import sys
import time
import requests

BASE    = "http://localhost:8000"
ADMIN   = "clk-admin-change-me-in-prod"
HEADERS = {"X-API-Key": ADMIN}
OLLAMA  = "http://localhost:11434"
SEP     = "=" * 64


def _req(method: str, path: str, body: dict = None, timeout: int = 90) -> dict:
    try:
        r = requests.request(
            method, f"{BASE}{path}",
            headers={**HEADERS, "Content-Type": "application/json"},
            json=body, timeout=timeout,
        )
        return {"code": r.status_code, "data": r.json(), "ok": r.status_code < 300}
    except requests.exceptions.ConnectionError:
        return {"code": 0, "data": {"detail": "API not reachable"}, "ok": False}
    except Exception as e:
        return {"code": 0, "data": {"detail": str(e)}, "ok": False}


def check_ollama() -> dict:
    try:
        r = requests.get(f"{OLLAMA}/api/tags", timeout=4)
        if r.status_code == 200:
            return {"running": True, "models": [m["name"] for m in r.json().get("models", [])]}
    except Exception:
        pass
    return {"running": False, "models": []}


def print_setup_instructions():
    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║           OLLAMA SETUP REQUIRED                      ║")
    print("  ║                                                      ║")
    print("  ║  Step 1 — Install Ollama (Windows):                  ║")
    print("  ║    winget install Ollama.Ollama                      ║")
    print("  ║    OR: https://ollama.com/download                   ║")
    print("  ║                                                      ║")
    print("  ║  Step 2 — Pull required models:                      ║")
    print("  ║    ollama pull llama3.2                              ║")
    print("  ║    ollama pull nomic-embed-text                      ║")
    print("  ║                                                      ║")
    print("  ║  Step 3 — Start Ollama server:                       ║")
    print("  ║    ollama serve                                      ║")
    print("  ║    (auto-starts after install on most systems)       ║")
    print("  ║                                                      ║")
    print("  ║  Step 4 — Re-run this demo:                          ║")
    print("  ║    python demo/demo_rag.py                           ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print()

def demo_status() -> bool:
    print(SEP)
    print("  SCENARIO 1 — RAG SYSTEM STATUS")
    print(SEP)
    ollama = check_ollama()
    print(f"\n  Ollama server  : {'RUNNING' if ollama['running'] else 'OFFLINE'}")
    for m in ollama["models"]:
        print(f"    Model: {m}")
    r = _req("GET", "/api/v1/rag/status")
    print(f"  API /rag/status: HTTP {r['code']}")
    if r["ok"]:
        d  = r["data"]
        vs = d.get("vector_store") or {}
        print(f"    ready        = {d.get('ready')}")
        print(f"    llm_model    = {d.get('llm_model', 'N/A')}")
        print(f"    vector_store = {vs.get('backend','N/A')} | {vs.get('total_mappings',0)} mappings")
    if not ollama["running"]:
        print_setup_instructions()
        return False
    r2 = _req("GET", "/api/v1/rag/models")
    if r2["ok"]:
        print(f"  Available models: {', '.join(r2['data'].get('models', []))}")
        print(f"  Active model    : {r2['data'].get('active')}")
    return True


def demo_field_mapping():
    print(f"\n{SEP}")
    print("  SCENARIO 2 — SINGLE FIELD MAPPING  (RAG + LLM)")
    print(SEP)
    fields = [
        {"field_name": "date_of_birth",        "field_type": "date",
         "fhir_resource": "Patient",    "sample_values": ["1990-05-15", "1985-11-30"]},
        {"field_name": "first_name",            "field_type": "varchar",
         "fhir_resource": "Patient",    "sample_values": ["Ahmed", "Sara", "Ali"]},
        {"field_name": "blood_glucose_level",   "field_type": "decimal",
         "fhir_resource": "Observation","sample_values": [5.4, 7.2, 6.8]},
        {"field_name": "prescribed_drug_name",  "field_type": "varchar",
         "fhir_resource": "MedicationRequest", "sample_values": ["Metformin", "Lisinopril"]},
        {"field_name": "admission_date",        "field_type": "datetime",
         "fhir_resource": "Encounter",  "sample_values": ["2024-01-15 09:00"]},
    ]
    print(f"\n  {'Field':<28} {'Type':<10} {'FHIR Path':<40} Conf  [Level]")
    print(f"  {'-'*28} {'-'*10} {'-'*40} ----  -------")
    confs = []
    for f in fields:
        r = _req("POST", "/api/v1/rag/suggest/field", f, timeout=120)
        if r["ok"]:
            d = r["data"]
            c = d.get("confidence", 0)
            confs.append(c)
            lvl = "HIGH" if c >= 0.8 else ("MED" if c >= 0.5 else "LOW")
            print(f"  {f['field_name']:<28} {f['field_type']:<10}"
                  f" {d.get('target_path','?'):<40} {c:.0%}  [{lvl}]")
        else:
            print(f"  {f['field_name']:<28} FAILED: {r['data'].get('detail','')[:40]}")
    if confs:
        avg  = sum(confs) / len(confs)
        high = sum(1 for c in confs if c >= 0.8)
        print(f"\n  Result: {len(confs)} fields | avg confidence {avg:.0%}"
              f" | {high}/{len(confs)} high-confidence (>=80%)")


def demo_schema_mapping():
    print(f"\n{SEP}")
    print("  SCENARIO 3 — FULL SCHEMA MAPPING  (unknown hospital table)")
    print(SEP)
    schema = {
        "table_name": "patient_registry",
        "fhir_resource": "Patient",
        "columns": [
            {"name": "pt_id",      "type": "integer"},
            {"name": "pt_mrn",     "type": "varchar"},
            {"name": "fname",      "type": "varchar"},
            {"name": "lname",      "type": "varchar"},
            {"name": "dob",        "type": "date"},
            {"name": "sex",        "type": "char"},
            {"name": "mobile_no",  "type": "varchar"},
            {"name": "email_addr", "type": "varchar"},
            {"name": "home_city",  "type": "varchar"},
        ],
    }
    print(f"\n  Table  : {schema['table_name']}  →  FHIR {schema['fhir_resource']}")
    print(f"  Columns: {len(schema['columns'])} unknown fields to auto-map with RAG\n")
    r = _req("POST", "/api/v1/rag/suggest/schema", schema, timeout=300)
    if not r["ok"]:
        print(f"  FAILED: {r['data'].get('detail','?')}")
        return
    d = r["data"]
    print(f"  {'Column':<20} {'FHIR Path':<44} Conf")
    print(f"  {'-'*20} {'-'*44} ----")
    for m in d.get("mappings", []):
        c    = m.get("confidence", 0)
        icon = "✓" if c >= 0.8 else ("~" if c >= 0.5 else "?")
        print(f"  {m.get('source_field',''):<20} {icon} {m.get('target_path',''):<43} {c:.0%}")
    s = d.get("statistics", {})
    print(f"\n  Accuracy: {d.get('accuracy_pct',0):.1f}%"
          f"  |  High: {s.get('high',0)}  Med: {s.get('medium',0)}  Low: {s.get('low',0)}")


def demo_confirm():
    print(f"\n{SEP}")
    print("  SCENARIO 4 — HUMAN CONFIRMATION  (learning loop)")
    print(SEP)
    confirms = [
        {"source_field": "pt_mrn", "source_type": "varchar",
         "target_path": "Patient.identifier[0].value",
         "fhir_resource": "Patient", "transformation": "none"},
        {"source_field": "sex", "source_type": "char",
         "target_path": "Patient.gender",
         "fhir_resource": "Patient", "transformation": "normalize_gender"},
    ]
    print("\n  Admin confirms 2 mappings → saved to vector store for future queries\n")
    for c in confirms:
        r = _req("POST", "/api/v1/rag/confirm", c)
        ok  = r["ok"] and r["data"].get("saved")
        tag = "SAVED" if ok else "FAILED"
        print(f"  {c['source_field']:<15} → {c['target_path']:<44} [{tag}]")
    r2 = _req("GET", "/api/v1/rag/knowledge-base")
    if r2["ok"]:
        vs = r2["data"].get("vector_store", {})
        print(f"\n  Vector store: {vs.get('total_mappings','?')} mappings ({vs.get('backend','?')})")


def demo_chat():
    print(f"\n{SEP}")
    print("  SCENARIO 5 — CLINICAL Q&A CHAT  (grounded on live FHIR DB)")
    print(SEP)
    questions = [
        "How many patients are currently in the system?",
        "What is the gender distribution of patients?",
        "What is the data quality breakdown of patient records?",
        "Which medications are most commonly prescribed?",
        "How many encounters are recorded and what types?",
    ]
    print(f"\n  {len(questions)} clinical questions answered from live FHIR data\n")
    for q in questions:
        print(f"  Q: {q}")
        r = _req("POST", "/api/v1/rag/chat", {"question": q}, timeout=120)
        if r["ok"]:
            d      = r["data"]
            answer = d.get("answer", "").strip()
            words, line, lines = answer.split(), "", []
            for w in words:
                if len(line) + len(w) + 1 > 68:
                    lines.append(line); line = w
                else:
                    line += (" " if line else "") + w
            if line:
                lines.append(line)
            for i, ln in enumerate(lines):
                print(f"  {'A:' if i == 0 else '  '} {ln}")
            grounded = "grounded" if d.get("grounded") else "ungrounded"
            print(f"     [{d.get('model','?')} | {d.get('latency_ms',0)}ms | {grounded}]")
        else:
            print(f"  A: FAILED — {r['data'].get('detail','?')}")
        print()


def main():
    print(f"\n{SEP}")
    print("  CARELOCK SYNC  —  SPRINT 4: RAG DEMO")
    print("  Ollama local LLM + ChromaDB + FHIR Mapping + Clinical Q&A")
    print(SEP)

    ok = demo_status()
    if not ok:
        print("  Ollama is required. Install it first, then re-run.\n")
        sys.exit(0)

    input("\n  [Enter] to run field mapping demo...")
    demo_field_mapping()

    input("\n  [Enter] to run schema mapping demo...")
    demo_schema_mapping()

    input("\n  [Enter] to run confirmation / learning demo...")
    demo_confirm()

    input("\n  [Enter] to run clinical Q&A demo...")
    demo_chat()

    print(f"\n{SEP}")
    print("  SPRINT 4 DEMO COMPLETE")
    print(SEP)
    print()


if __name__ == "__main__":
    main()
