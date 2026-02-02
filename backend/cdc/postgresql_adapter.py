"""
PostgreSQL CDC Adapter - Trigger-based
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cdc.base_adapter import CDCAdapter, ChangeEvent, OperationType
from sqlalchemy import create_engine, text
from typing import List, Optional


class PostgreSQLAdapter(CDCAdapter):
    """PostgreSQL trigger-based CDC adapter"""
    
    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        self.engine = create_engine(connection_string)
    
    def get_database_type(self) -> str:
        return "postgresql"
    
    def setup_cdc(self, tables: List[str]) -> bool:
        """Setup CDC triggers for PostgreSQL tables"""
        try:
            from connector.cdc_monitor import CDCMonitor
            monitor = CDCMonitor(self.connection_string)
            
            for table in tables:
                monitor.add_trigger_to_table(table)
            
            self.is_setup = True
            return True
        except Exception as e:
            print(f"PostgreSQL CDC setup failed: {e}")
            return False
    
    def get_changes(
        self, 
        since_change_id: Optional[int] = None,
        table_name: Optional[str] = None,
        limit: int = 100
    ) -> List[ChangeEvent]:
        """Get changes from data_change_log table"""
        changes = []
        
        try:
            with self.engine.connect() as conn:
                query = """
                    SELECT change_id, table_name, operation, 
                           record_id, old_data, new_data, changed_at
                    FROM data_change_log
                    WHERE 1=1
                """
                params = {}
                
                if since_change_id is not None:
                    query += " AND change_id > :since_id"
                    params['since_id'] = since_change_id
                
                if table_name:
                    query += " AND table_name = :table_name"
                    params['table_name'] = table_name
                
                query += " ORDER BY change_id LIMIT :limit"
                params['limit'] = limit
                
                result = conn.execute(text(query), params)
                
                for row in result:
                    changes.append(ChangeEvent(
                        change_id=row[0],
                        table_name=row[1],
                        operation=OperationType[row[2]],
                        record_id=row[3],
                        old_data=row[4],
                        new_data=row[5],
                        changed_at=row[6],
                        database_type='postgresql'
                    ))
        except Exception as e:
            print(f"Error getting PostgreSQL changes: {e}")
        
        return changes
    
    def get_latest_change_id(self) -> Optional[int]:
        """Get the latest change ID"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT MAX(change_id) FROM data_change_log"
                ))
                return result.scalar()
        except Exception as e:
            return None
    
    def is_cdc_enabled(self, table_name: str) -> bool:
        """Check if CDC trigger exists for table"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.triggers
                    WHERE event_object_table = :table_name
                    AND trigger_name LIKE '%_change_trigger'
                """), {'table_name': table_name})
                return result.scalar() > 0
        except Exception as e:
            return False
    
    def validate_connection(self) -> bool:
        """Validate PostgreSQL connection"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            return False
