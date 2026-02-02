"""
CDC Adapter Factory
"""
from typing import List
from cdc.base_adapter import CDCAdapter
from cdc.postgresql_adapter import PostgreSQLAdapter


class CDCAdapterFactory:
    """Factory to create appropriate CDC adapter"""
    
    @staticmethod
    def create_adapter(connection_string: str) -> CDCAdapter:
        """Create appropriate CDC adapter based on connection string"""
        conn_lower = connection_string.lower()
        
        if 'postgresql://' in conn_lower or 'postgres://' in conn_lower:
            return PostgreSQLAdapter(connection_string)
        
        elif 'mysql://' in conn_lower:
            try:
                from cdc.mysql_adapter import MySQLAdapter
                return MySQLAdapter(connection_string)
            except ImportError:
                raise ImportError(
                    "MySQL adapter requires: pip install pymysqlreplication PyMySQL"
                )
        
        elif 'mongodb://' in conn_lower or 'mongodb+srv://' in conn_lower:
            try:
                from cdc.mongodb_adapter import MongoDBAdapter
                return MongoDBAdapter(connection_string)
            except ImportError:
                raise ImportError(
                    "MongoDB adapter requires: pip install pymongo"
                )
        
        else:
            raise ValueError(
                f"Unsupported database type. Supported: postgresql, mysql, mongodb"
            )
    
    @staticmethod
    def get_supported_databases() -> List[str]:
        """Get list of supported database types"""
        return ['postgresql', 'mysql', 'mongodb']
    
    @staticmethod
    def detect_database_type(connection_string: str) -> str:
        """Detect database type from connection string"""
        conn_lower = connection_string.lower()
        
        if 'postgresql://' in conn_lower or 'postgres://' in conn_lower:
            return 'postgresql'
        elif 'mysql://' in conn_lower:
            return 'mysql'
        elif 'mongodb://' in conn_lower or 'mongodb+srv://' in conn_lower:
            return 'mongodb'
        else:
            raise ValueError(f"Unsupported database type")
