import os, shutil
env_path = r'C:\Projects\CareLock-Sync\config\.env'
with open(env_path, 'r') as f: content = f.read()
adds = []
if 'MAPPING_MODEL' not in content: adds.append('MAPPING_MODEL=llama3.2:3b')
if 'CHAT_MODEL' not in content: adds.append('CHAT_MODEL=phi3')
if 'CHROMA_PATH' not in content: adds.append('CHROMA_PATH=./databases/chroma')
if adds:
    with open(env_path, 'a') as f:
        f.write('\n# Sprint 4 v2 Dual-Model\n' + '\n'.join(adds) + '\n')
    print('Added to .env:', adds)
else:
    print('.env already up to date')

chroma = r'C:\Projects\CareLock-Sync\databases\chroma'
if os.path.exists(chroma):
    shutil.rmtree(chroma)
    print('Old ChromaDB wiped')
os.makedirs(chroma, exist_ok=True)
print('ChromaDB directory ready')
