import requests, json

# 1. Ollama connectivity
r = requests.get('http://localhost:11434/api/tags', timeout=5)
models = [m['name'] for m in r.json().get('models', [])]
print('Ollama: HTTP', r.status_code)
print('Models:', models)

# 2. phi3 generation test
print()
print('Testing phi3 generation...')
resp = requests.post('http://localhost:11434/api/generate', json={
    'model': 'phi3',
    'prompt': 'Map field "date_of_birth" (date) to FHIR Patient. Reply ONLY JSON: {"target_path": "...", "confidence": 0.9}',
    'stream': False,
    'options': {'temperature': 0.1, 'num_predict': 50}
}, timeout=90)
print('phi3 HTTP:', resp.status_code)
print('phi3 response:', resp.json().get('response', '')[:120])

# 3. nomic-embed-text test
print()
print('Testing nomic-embed-text embeddings...')
resp2 = requests.post('http://localhost:11434/api/embeddings', json={
    'model': 'nomic-embed-text',
    'prompt': 'date_of_birth date Patient birthDate'
}, timeout=30)
emb = resp2.json().get('embedding', [])
print('Embedding dim:', len(emb))
print('nomic-embed-text: OK' if len(emb) > 0 else 'FAILED')
