"""Test RAG-Powered Mapping with Gemini"""
import sys
import os
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from rag.mapping_suggester import MappingSuggester

print("=" * 70)
print("Phase 3: RAG-Powered Mapping Test")
print("=" * 70)

# Check API key
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in environment")
    exit(1)

print(f"\n[Test 1] Gemini API Key: {'*' * 20}{api_key[-10:]} [OK]")

# Initialize RAG suggester
print("\n[Test 2] Initializing RAG Suggester...")
try:
    suggester = MappingSuggester(
        gemini_api_key=api_key,
        vector_store_path=r"C:\Projects\CareLock-Sync\chroma_db",
        auto_load_existing=True
    )
    print("  RAG Suggester initialized [OK]")
except Exception as e:
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test single field mapping
print("\n[Test 3] Single Field Mapping:")
try:
    result = suggester.suggest_mapping(
        field_name='patient_dob',
        field_type='date',
        sample_values=['1990-01-15', '1985-03-22'],
        fhir_resource='Patient'
    )
    
    print(f"\n  Field: {result['source_field']}")
    print(f"  Suggested Path: {result['target_path']}")
    print(f"  Confidence: {result['confidence']:.0%}")
    print(f"  Transformation: {result['transformation']}")
    print(f"  Reasoning: {result['reasoning'][:80]}...")
    print("  [OK]")
    
except Exception as e:
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()

# Test schema mapping
print("\n[Test 4] Complete Schema Mapping:")
try:
    schema = {
        'table_name': 'new_patients',
        'columns': [
            {'name': 'mrn', 'type': 'varchar'},
            {'name': 'full_name', 'type': 'varchar'},
            {'name': 'birth_date', 'type': 'date'},
            {'name': 'sex', 'type': 'char'}
        ]
    }
    
    result = suggester.suggest_schema_mapping(schema, fhir_resource='Patient')
    
    print("\n  AI-Suggested Mappings:")
    for mapping in result['mappings']:
        print(f"    {mapping['source_field']:15} -> {mapping['target_path']:30} ({mapping['confidence']:.0%})")
    
    print("\n  [SUCCESS] Schema mapping complete!")
    
except Exception as e:
    print(f"  Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("RAG Test Complete!")
print("=" * 70)
