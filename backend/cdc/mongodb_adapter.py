"""
MongoDB CDC Adapter - Change Log based
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cdc.base_adapter import CDCAdapter, ChangeEvent, OperationType
from typing import List, Optional
from datetime import datetime

try:
    from pymongo import MongoClient
    from bson import ObjectId
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False


class MongoDBAdapter(CDCAdapter):
    """MongoDB change log CDC adapter"""
    
    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        if not MONGODB_AVAILABLE:
            raise ImportError("MongoDB adapter requires: pip install pymongo")
        
        # Parse: mongodb://localhost:27017/database
        parts = connection_string.replace('mongodb://', '').split('/')
        self.host = parts[0]
        self.database_name = parts[1] if len(parts) > 1 else 'hospital_db_mongodb'
        self.client = MongoClient(f'mongodb://{self.host}/')
        self.db = self.client[self.database_name]
    
    def get_database_type(self) -> str:
        return "mongodb"
    
    def setup_cdc(self, collections: List[str]) -> bool:
        """Setup CDC collection for MongoDB"""
        try:
            if 'change_log' not in self.db.list_collection_names():
                self.db.create_collection('change_log')
            
            self.db.change_log.create_index('table_name')
            self.db.change_log.create_index('changed_at')
            
            print("  [OK] MongoDB change_log collection ready")
            self.is_setup = True
            return True
        except Exception as e:
            print(f"MongoDB CDC setup failed: {e}")
            return False
    
    def log_change(self, collection: str, operation: str, document_id, old_data=None, new_data=None):
        """Manually log a change"""
        self.db.change_log.insert_one({
            'table_name': collection,
            'operation': operation,
            'record_id': str(document_id),
            'old_data': old_data,
            'new_data': new_data,
            'changed_at': datetime.utcnow()
        })
    
    def get_changes(self, since_change_id=None, table_name=None, limit=100) -> List[ChangeEvent]:
        """Get changes from change_log"""
        try:
            query = {}
            
            if since_change_id:
                query['_id'] = {'$gt': ObjectId(since_change_id)}
            
            if table_name:
                query['table_name'] = table_name
            
            cursor = self.db.change_log.find(query).sort('_id', 1).limit(limit)
            
            changes = []
            for doc in cursor:
                changes.append(ChangeEvent(
                    change_id=str(doc['_id']),
                    table_name=doc['table_name'],
                    operation=OperationType[doc['operation']],
                    record_id=doc.get('record_id'),
                    old_data=doc.get('old_data'),
                    new_data=doc.get('new_data'),
                    changed_at=doc.get('changed_at'),
                    database_type='mongodb'
                ))
            
            return changes
        except Exception as e:
            print(f"Error getting MongoDB changes: {e}")
            return []
    
    def get_latest_change_id(self) -> Optional[str]:
        try:
            latest = self.db.change_log.find_one(sort=[('_id', -1)])
            return str(latest['_id']) if latest else None
        except:
            return None
    
    def validate_connection(self) -> bool:
        try:
            self.client.admin.command('ping')
            return True
        except Exception as e:
            print(f"MongoDB validation failed: {e}")
            return False
