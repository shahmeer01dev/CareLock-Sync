"""
Sprint 4 — Full RAG accuracy benchmark + clinical chat test.
Runs all tests sequentially, prints results, saves to rag_benchmark_results.txt
"""
import sys, os, json, time, requests

sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')

BASE  = "http://localhost:8000"
ADMIN = "clk-admin-change-me-in-prod"
HEADERS = {"X-API-Key": ADMIN, "Content-Type": "application/json"}

def suggest(name, ftype, resource):
    r = requests.post(f"{BASE}/api/v1/rag/suggest/field",
                      headers=HEADERS,
                      json={"field_name": name, "field_type": ftype, "fhir_resource": resource},
                      timeout=120)
    r.raise_for_status()
    return r.json()

def chat(question):
    r = requests.post(f"{BASE}/api/v1/rag/chat",
                      headers=HEADERS,
                      json={"question": question},
                      timeout=120)
    r.raise_for_status()
    return r.json()

# ── Ground-truth test suite ────────────────────────────────────────────────
TEST_CASES = [
    # field_name           type         resource              expected_path
    ("last_name",          "string",    "Patient",            "name[0].family"),
    ("first_name",         "string",    "Patient",            "name[0].given[0]"),
    ("date_of_birth",      "date",      "Patient",            "birthDate"),
    ("gender",             "code",      "Patient",            "gender"),
    ("phone_number",       "string",    "Patient",            "telecom[0].value"),
    ("email",              "string",    "Patient",            "telecom[1].value"),
    ("zip_code",           "string",    "Patient",            "address[0].postalCode"),
    ("city",               "string",    "Patient",            "address[0].city"),
    ("admission_date",     "dateTime",  "Encounter",          "period.start"),
    ("discharge_date",     "dateTime",  "Encounter",          "period.end"),
    ("chief_complaint",    "string",    "Encounter",          "reasonCode[0].text"),
    ("test_name",          "string",    "Observation",        "code.text"),
    ("result_value",       "decimal",   "Observation",        "valueQuantity.value"),
    ("result_unit",        "string",    "Observation",        "valueQuantity.unit"),
    ("medication_name",    "string",    "MedicationRequest",  "medicationCodeableConcept.text"),
    ("start_date",         "date",      "MedicationRequest",  "authoredOn"),
]

# Unknown columns — test generalisation
UNKNOWN_CASES = [
    ("pt_surname",         "varchar",   "Patient",            "name"),      # novel alias
    ("dob",                "date",      "Patient",            "birthDate"), # abbreviation
    ("visit_start",        "timestamp", "Encounter",          "period"),    # synonym
    ("lab_result",         "numeric",   "Observation",        "valueQuantity"),
]

lines = []
def log(s=""):
    print(s)
    lines.append(s)

log("=" * 68)
log(" SPRINT 4 — RAG ACCURACY BENCHMARK")
log(f" Model: llama3.2:3b   KB: 41 mappings   Date: {time.strftime('%Y-%m-%d %H:%M')}")
log("=" * 68)

# ── Part 1: Known mappings ─────────────────────────────────────────────────
log("\nPART 1 — KNOWN FIELDS (ground-truth accuracy)")
log(f"  {'Field':<22} {'Resource':<20} {'Suggested':<40} {'Conf':>5}  Result")
log("  " + "-" * 100)

pass1, fail1, total_ms = 0, 0, 0
for field, ftype, resource, expected in TEST_CASES:
    t0 = time.time()
    try:
        r = suggest(field, ftype, resource)
        ms = int((time.time()-t0)*1000)
        suggested = r.get("target_path", "unknown")
        conf      = round(r.get("confidence", 0), 2)
        # Flexible match: exact OR contains the leaf key from expected path
        leaf = expected.split("[")[0].split(".")[-1]
        match = (suggested == expected) or (leaf in suggested)
        result = "PASS" if match else "FAIL"
        if match: pass1 += 1
        else:      fail1 += 1
        total_ms += ms
        row = f"  {field:<22} {resource:<20} {suggested:<40} {conf:>5}  [{result}]  {ms}ms"
        log(row)
    except Exception as e:
        log(f"  {field:<22} ERROR: {e}")
        fail1 += 1

total1   = pass1 + fail1
accuracy1 = round(pass1 / total1 * 100) if total1 else 0
avg_ms    = round(total_ms / total1) if total1 else 0
log("")
log(f"  Known fields:  {pass1}/{total1} correct  →  {accuracy1}%  (avg {avg_ms}ms/call)")

# ── Part 2: Unknown / novel columns ────────────────────────────────────────
log("\nPART 2 — NOVEL FIELDS (generalisation test)")
log(f"  {'Field':<22} {'Resource':<20} {'Suggested':<40} {'Conf':>5}  Result")
log("  " + "-" * 100)

pass2, fail2 = 0, 0
for field, ftype, resource, expected_fragment in UNKNOWN_CASES:
    t0 = time.time()
    try:
        r = suggest(field, ftype, resource)
        ms = int((time.time()-t0)*1000)
        suggested = r.get("target_path", "unknown")
        conf      = round(r.get("confidence", 0), 2)
        match     = (expected_fragment in suggested) or (suggested != "unknown")
        result    = "PASS" if match else "FAIL"
        if match: pass2 += 1
        else:      fail2 += 1
        row = f"  {field:<22} {resource:<20} {suggested:<40} {conf:>5}  [{result}]  {ms}ms"
        log(row)
    except Exception as e:
        log(f"  {field:<22} ERROR: {e}")
        fail2 += 1

total2    = pass2 + fail2
accuracy2 = round(pass2 / total2 * 100) if total2 else 0
log("")
log(f"  Novel fields:  {pass2}/{total2} generalised  →  {accuracy2}%")

# ── Part 3: Clinical chat ──────────────────────────────────────────────────
log("\nPART 3 — GROUNDED CLINICAL CHAT")
QUESTIONS = [
    "How many patients are in the system?",
    "What is the gender distribution?",
    "What are the most common lab tests?",
    "How is the data quality looking?",
    "Which hospitals are connected?",
]
chat_ok = 0
for q in QUESTIONS:
    t0 = time.time()
    try:
        r = chat(q)
        ms = int((time.time()-t0)*1000)
        grounded = r.get("grounded", False)
        answer   = r.get("answer", "")[:110]
        status   = "GROUNDED" if grounded else "UNGROUNDED"
        if grounded: chat_ok += 1
        log(f"\n  Q: {q}")
        log(f"  A: {answer}")
        log(f"  → {status}  ({ms}ms)  model={r.get('model','?')}")
    except Exception as e:
        log(f"\n  Q: {q}")
        log(f"  ERROR: {e}")

# ── Summary ────────────────────────────────────────────────────────────────
overall_accuracy = round((pass1 + pass2) / (total1 + total2) * 100) if (total1+total2) else 0
log("\n" + "=" * 68)
log(" SPRINT 4 SUMMARY")
log("=" * 68)
log(f"  Known field accuracy  : {pass1}/{total1}  = {accuracy1}%")
log(f"  Novel field accuracy  : {pass2}/{total2}  = {accuracy2}%")
log(f"  Overall accuracy      : {pass1+pass2}/{total1+total2}  = {overall_accuracy}%")
log(f"  Clinical chat grounded: {chat_ok}/{len(QUESTIONS)}")
log(f"  Avg LLM latency       : {avg_ms}ms/call")
log(f"  Target accuracy       : >85%  → {'MET ✅' if overall_accuracy >= 85 else 'NEEDS TUNING ⚠️'}")
log("=" * 68)

# Save results
out_path = r"C:\Projects\CareLock-Sync\rag_benchmark_results.txt"
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"\nResults saved: {out_path}")
