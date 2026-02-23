import sys
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
from rag.vector_store import MappingVectorStore

chroma_path = r'C:\Projects\CareLock-Sync\databases\chroma'
vs = MappingVectorStore(persist_directory=chroma_path)
print(f'Current count: {vs.count()}')

# Force reload all 4 FHIR resource mappings with proper nomic-embed-text embeddings
loaded = vs.load_all_fhir_mappings()
print(f'Total after reload: {vs.count()}')

# Test similarity search
tests = [
    ('date_of_birth', 'date'),
    ('first_name', 'string'),
    ('result_value', 'decimal'),
    ('medication_name', 'string'),
    ('encounter_type', 'code'),
]
print('\n--- Similarity Search Tests ---')
for field, ftype in tests:
    results = vs.find_similar_mappings(field, ftype, n_results=2)
    if results:
        best = results[0]
        print(f'  {field} -> {best["target_path"]} [{best["fhir_resource"]}] sim={best["similarity"]}')
    else:
        print(f'  {field} -> NO RESULTS')

print('\nVector store pre-load COMPLETE')
