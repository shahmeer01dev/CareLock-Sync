"""
RAG-Powered Mapping Suggester - Main Intelligence Engine
"""
from typing import Dict, List, Any, Optional
from rag.gemini_client import GeminiClient
from rag.vector_store import MappingVectorStore
import os


class MappingSuggester:
    """RAG-based system for intelligent FHIR field mapping"""
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        vector_store_path: str = "./chroma_db",
        auto_load_existing: bool = True
    ):
        """Initialize RAG mapping suggester"""
        self.gemini = GeminiClient(gemini_api_key)
        self.vector_store = MappingVectorStore(persist_directory=vector_store_path)
        
        if auto_load_existing:
            self.load_existing_mappings()
    
    def load_existing_mappings(self):
        """Load existing mappings as training data"""
        print("Loading existing FHIR mappings...")
        count = self.vector_store.load_from_mapping_config()
        print(f"Loaded {count} existing mappings")
    
    def suggest_mapping(
        self,
        field_name: str,
        field_type: str,
        sample_values: Optional[List] = None,
        fhir_resource: str = 'Patient',
        n_similar: int = 5
    ) -> Dict[str, Any]:
        """Suggest FHIR mapping for a single field"""
        print(f"Suggesting mapping for: {field_name} ({field_type})")
        
        # RAG Retrieval - Find similar mappings
        similar_mappings = self.vector_store.find_similar_mappings(
            field_name=field_name,
            field_type=field_type,
            n_results=n_similar,
            min_similarity=0.3
        )
        
        print(f"  Found {len(similar_mappings)} similar mappings")
        
        # RAG Generation - Use Gemini
        suggestion = self.gemini.generate_mapping_suggestion(
            source_field={
                'name': field_name,
                'type': field_type,
                'sample_values': sample_values or []
            },
            similar_mappings=similar_mappings,
            fhir_resource=fhir_resource
        )
        
        # Augment with retrieval results
        suggestion['source_field'] = field_name
        suggestion['source_type'] = field_type
        suggestion['fhir_resource'] = fhir_resource
        suggestion['similar_mappings'] = similar_mappings
        
        print(f"  Suggested: {suggestion['target_path']} ({suggestion['confidence']:.0%})")
        
        return suggestion
    
    def suggest_schema_mapping(
        self,
        schema: Dict[str, Any],
        fhir_resource: str = 'Patient'
    ) -> Dict[str, Any]:
        """Suggest FHIR mappings for entire schema"""
        print(f"\nSuggesting mappings for: {schema.get('table_name', 'unknown')}")
        print("=" * 70)
        
        mappings = []
        stats = {
            'total_fields': 0,
            'high_confidence': 0,
            'medium_confidence': 0,
            'low_confidence': 0,
            'needs_review': 0
        }
        
        for column in schema.get('columns', []):
            stats['total_fields'] += 1
            
            suggestion = self.suggest_mapping(
                field_name=column['name'],
                field_type=column['type'],
                sample_values=column.get('sample_values'),
                fhir_resource=fhir_resource
            )
            
            mappings.append(suggestion)
            
            confidence = suggestion['confidence']
            if confidence >= 0.8:
                stats['high_confidence'] += 1
            elif confidence >= 0.5:
                stats['medium_confidence'] += 1
            else:
                stats['low_confidence'] += 1
            
            if confidence < 0.7:
                stats['needs_review'] += 1
        
        print("\n" + "=" * 70)
        print("Schema Mapping Summary:")
        print(f"  Total Fields: {stats['total_fields']}")
        print(f"  High Confidence (>=80%): {stats['high_confidence']}")
        print(f"  Medium Confidence (50-80%): {stats['medium_confidence']}")
        print(f"  Low Confidence (<50%): {stats['low_confidence']}")
        print(f"  Needs Review: {stats['needs_review']}")
        print("=" * 70)
        
        return {
            'table_name': schema.get('table_name'),
            'fhir_resource': fhir_resource,
            'mappings': mappings,
            'statistics': stats
        }
    
    def save_mapping(self, mapping: Dict):
        """Save mapping for future learning"""
        self.vector_store.add_mapping(mapping)
        print(f"Saved: {mapping['source_field']} -> {mapping['target_path']}")
