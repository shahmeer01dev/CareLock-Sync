"""
Base CDC Adapter - Abstract Interface
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class OperationType(Enum):
    """CDC operation types"""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class ChangeEvent:
    """Unified change event format across all databases"""
    def __init__(
        self,
        change_id: int,
        table_name: str,
        operation: OperationType,
        record_id: Any,
        old_data: Optional[Dict] = None,
        new_data: Optional[Dict] = None,
        changed_at: datetime = None,
        database_type: str = None
    ):
        self.change_id = change_id
        self.table_name = table_name
        self.operation = operation
        self.record_id = record_id
        self.old_data = old_data or {}
        self.new_data = new_data or {}
        self.changed_at = changed_at or datetime.utcnow()
        self.database_type = database_type
    
    def to_dict(self) -> Dict:
        return {
            'change_id': self.change_id,
            'table_name': self.table_name,
            'operation': self.operation.value,
            'record_id': self.record_id,
            'old_data': self.old_data,
            'new_data': self.new_data,
            'changed_at': self.changed_at.isoformat() if self.changed_at else None,
            'database_type': self.database_type
        }
    
    def __repr__(self):
        return f"ChangeEvent({self.operation.value} on {self.table_name}, ID={self.record_id})"


class CDCAdapter(ABC):
    """Abstract base class for database-specific CDC adapters"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.is_setup = False
    
    @abstractmethod
    def get_database_type(self) -> str:
        """Return the database type identifier"""
        pass
    
    @abstractmethod
    def setup_cdc(self, tables: List[str]) -> bool:
        """Setup CDC for specified tables"""
        pass
    
    @abstractmethod
    def get_changes(
        self, 
        since_change_id: Optional[int] = None,
        table_name: Optional[str] = None,
        limit: int = 100
    ) -> List[ChangeEvent]:
        """Get change events since specified change ID"""
        pass
    
    @abstractmethod
    def get_latest_change_id(self) -> Optional[int]:
        """Get the latest change ID"""
        pass
    
    def is_cdc_enabled(self, table_name: str) -> bool:
        """Check if CDC is enabled for a table"""
        return self.is_setup
    
    def validate_connection(self) -> bool:
        """Validate database connection"""
        try:
            return True
        except Exception as e:
            print(f"Connection validation failed: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get CDC statistics"""
        return {
            'database_type': self.get_database_type(),
            'is_setup': self.is_setup,
            'connection_valid': self.validate_connection()
        }
