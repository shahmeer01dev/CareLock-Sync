"""
Vector Store for Field Mapping Similarity Search
"""
from typing import List, Dict, Any, Optional
import json


class MappingVectorStore:
    """ChromaDB-based vector store"""
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB"""
        try:
            import chromadb
            from chromadb.config import Settings
            self.chromadb = chromadb
        except ImportError:
            raise ImportError("Run: pip install chromadb")
        
        self.client = self.chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        
        self.collection = self.client.get_or_create_collection(
            name="field_mappings",
            metadata={"description": "FHIR mapping knowledge"}
        )
        
        print(f"Vector store: {self.collection.count()} mappings loaded")
    
    def add_mapping(self, mapping: Dict[str, Any]) -> bool:
        """Add field mapping to vector store"""
        try:
            embedding_text = self._create_embedding_text(mapping)
            mapping_id = f"mapping_{abs(hash(embedding_text))}"
            
            self.collection.add(
                documents=[embedding_text],
                metadatas=[{
                    'source_field': mapping.get('source_field', ''),
                    'source_type': mapping.get('source_type', ''),
                    'target_path': mapping.get('target_path', ''),
                    'database_type': mapping.get('database_type', 'unknown'),
                    'confidence': float(mapping.get('confidence', 0.0)),
                    'transformation': mapping.get('transformation', 'none')
                }],
                ids=[mapping_id]
            )
            return True
        except Exception as e:
            print(f"Error adding mapping: {e}")
            return False
    
    def _create_embedding_text(self, mapping: Dict) -> str:
        """Create text for embedding"""
        parts = []
        if 'source_field' in mapping:
            field_name = mapping['source_field']
            parts.append(field_name)
            parts.append(field_name.replace('_', ' '))
        if 'source_type' in mapping:
            parts.append(mapping['source_type'])
        if 'target_path' in mapping:
            target = mapping['target_path']
            parts.append(target)
            if '.' in target:
                parts.append(target.split('.')[-1])
        return ' '.join(parts)
    
    def find_similar_mappings(
        self,
        field_name: str,
        field_type: str,
        n_results: int = 5,
        min_similarity: float = 0.0
    ) -> List[Dict]:
        """Find similar field mappings"""
        try:
            query_text = f"{field_name} {field_name.replace('_', ' ')} {field_type}"
            
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            similar_mappings = []
            if results['metadatas'] and results['distances']:
                for metadata, distance in zip(
                    results['metadatas'][0],
                    results['distances'][0]
                ):
                    similarity = 1.0 - distance
                    if similarity >= min_similarity:
                        similar_mappings.append({
                            **metadata,
                            'similarity': round(similarity, 4)
                        })
            
            return similar_mappings
        except Exception as e:
            print(f"Error finding similar: {e}")
            return []
    
    def load_training_data(self, mappings: List[Dict]) -> int:
        """Load multiple mappings"""
        count = 0
        for mapping in mappings:
            if self.add_mapping(mapping):
                count += 1
        print(f"Loaded {count}/{len(mappings)} training mappings")
        return count
    
    def load_from_mapping_config(self):
        """Load existing mappings from MappingConfig"""
        try:
            import sys
            import os
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sys.path.insert(0, backend_dir)
            
            from schema_mapper.mapping_config import MappingConfig
            
            training_data = []
            
            for field_mapping in MappingConfig.PATIENT_MAPPING['field_mappings']:
                training_data.append({
                    'source_field': field_mapping['source_field'],
                    'source_type': field_mapping['data_type'],
                    'target_path': field_mapping['target_path'],
                    'database_type': 'postgresql',
                    'confidence': 0.95,
                    'transformation': field_mapping.get('transformation', 'none')
                })
            
            for field_mapping in MappingConfig.ENCOUNTER_MAPPING['field_mappings']:
                training_data.append({
                    'source_field': field_mapping['source_field'],
                    'source_type': field_mapping['data_type'],
                    'target_path': field_mapping['target_path'],
                    'database_type': 'postgresql',
                    'confidence': 0.95,
                    'transformation': field_mapping.get('transformation', 'none')
                })
            
            return self.load_training_data(training_data)
        except Exception as e:
            print(f"Error loading from MappingConfig: {e}")
            return 0
    
    def get_statistics(self) -> Dict:
        """Get vector store statistics"""
        return {
            'total_mappings': self.collection.count(),
            'collection_name': self.collection.name
        }
