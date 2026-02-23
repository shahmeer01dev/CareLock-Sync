import os, sys
root = r'C:\Projects\CareLock-Sync'
checks = [
    ('backend/rag/ollama_client.py','ollama_client'),
    ('backend/rag/mapping_suggester.py','mapping_suggester'),
    ('backend/api/routes/rag.py','routes/rag'),
    ('backend/rag/vector_store.py','vector_store'),
    ('backend/rag/fhir_knowledge.py','fhir_knowledge'),
]
for relpath, label in checks:
    full = os.path.join(root, relpath.replace('/',chr(92)))
    c = open(full,'r',encoding='utf-8',errors='replace').read()
    phi3    = 'phi3' in c
    mistral = 'mistral' in c
    newapi  = 'PersistentClient' in c
    gemini  = 'gemini' in c.lower()
    entries = c.count('source_field')
    size    = len(c)
    print(f'{label}: phi3={phi3} mistral={mistral} newChroma={newapi} gemini={gemini} entries={entries} size={size}')
