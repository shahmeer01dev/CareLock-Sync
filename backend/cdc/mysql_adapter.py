"""
MySQL CDC Adapter - Trigger-based Change Data Capture
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cdc.base_adapter import CDCAdapter, ChangeEvent, OperationType
from typing import List, Optional

try:
    import pymysql
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False


class MySQLAdapter(CDCAdapter):
    """MySQL trigger-based CDC adapter"""
    
    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        if not MYSQL_AVAILABLE:
            raise ImportError("MySQL adapter requires: pip install pymysql")
        
        # Parse: mysql://user:pass@host:port/database
        parts = connection_string.replace('mysql://', '').split('@')
        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')
        host_port = host_db[0].split(':')
        
        self.config = {
            'host': host_port[0],
            'port': int(host_port[1]) if len(host_port) > 1 else 3306,
            'user': user_pass[0],
            'password': user_pass[1] if len(user_pass) > 1 else '',
            'database': host_db[1] if len(host_db) > 1 else '',
            'charset': 'utf8mb4'
        }
    
    def get_database_type(self) -> str:
        return "mysql"
    
    def setup_cdc(self, tables: List[str]) -> bool:
        """Setup CDC triggers for MySQL"""
        try:
            conn = pymysql.connect(**self.config, cursorclass=pymysql.cursors.DictCursor)
            cursor = conn.cursor()
            
            # Create change log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_change_log (
                    change_id BIGINT AUTO_INCREMENT PRIMARY KEY,
                    table_name VARCHAR(100) NOT NULL,
                    operation VARCHAR(10) NOT NULL,
                    record_id INT,
                    old_data JSON,
                    new_data JSON,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_table (table_name),
                    INDEX idx_time (changed_at)
                ) ENGINE=InnoDB
            """)
            
            for table in tables:
                # Get primary key
                cursor.execute(f"""
                    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = '{table}'
                    AND CONSTRAINT_NAME = 'PRIMARY' LIMIT 1
                """)
                pk = cursor.fetchone()
                pk_col = pk['COLUMN_NAME'] if pk else f'{table[:-1]}_id'
                
                # Drop old triggers
                for op in ['insert', 'update', 'delete']:
                    cursor.execute(f"DROP TRIGGER IF EXISTS {table}_after_{op}")
                
                # CREATE triggers
                cursor.execute(f"""
                    CREATE TRIGGER {table}_after_insert AFTER INSERT ON {table}
                    FOR EACH ROW
                    INSERT INTO data_change_log (table_name, operation, record_id, new_data)
                    VALUES ('{table}', 'INSERT', NEW.{pk_col}, JSON_OBJECT('{pk_col}', NEW.{pk_col}))
                """)
                
                cursor.execute(f"""
                    CREATE TRIGGER {table}_after_update AFTER UPDATE ON {table}
                    FOR EACH ROW
                    INSERT INTO data_change_log (table_name, operation, record_id, old_data, new_data)
                    VALUES ('{table}', 'UPDATE', NEW.{pk_col}, 
                            JSON_OBJECT('{pk_col}', OLD.{pk_col}),
                            JSON_OBJECT('{pk_col}', NEW.{pk_col}))
                """)
                
                cursor.execute(f"""
                    CREATE TRIGGER {table}_after_delete AFTER DELETE ON {table}
                    FOR EACH ROW
                    INSERT INTO data_change_log (table_name, operation, record_id, old_data)
                    VALUES ('{table}', 'DELETE', OLD.{pk_col}, JSON_OBJECT('{pk_col}', OLD.{pk_col}))
                """)
                
                print(f"  [OK] MySQL CDC triggers created for: {table}")
            
            conn.commit()
            conn.close()
            self.is_setup = True
            return True
        except Exception as e:
            print(f"MySQL CDC setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_changes(self, since_change_id=None, table_name=None, limit=100) -> List[ChangeEvent]:
        """Get changes from data_change_log"""
        try:
            conn = pymysql.connect(**self.config, cursorclass=pymysql.cursors.DictCursor)
            cursor = conn.cursor()
            
            query = "SELECT * FROM data_change_log WHERE 1=1"
            params = []
            if since_change_id:
                query += " AND change_id > %s"
                params.append(since_change_id)
            if table_name:
                query += " AND table_name = %s"
                params.append(table_name)
            query += " ORDER BY change_id LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            changes = [ChangeEvent(
                change_id=r['change_id'],
                table_name=r['table_name'],
                operation=OperationType[r['operation']],
                record_id=r['record_id'],
                old_data=r['old_data'],
                new_data=r['new_data'],
                changed_at=r['changed_at'],
                database_type='mysql'
            ) for r in cursor.fetchall()]
            
            conn.close()
            return changes
        except Exception as e:
            print(f"Error getting MySQL changes: {e}")
            return []
    
    def get_latest_change_id(self) -> Optional[int]:
        try:
            conn = pymysql.connect(**self.config)
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(change_id) FROM data_change_log")
            result = cursor.fetchone()
            conn.close()
            return result[0] if result and result[0] else None
        except:
            return None
    
    def validate_connection(self) -> bool:
        try:
            conn = pymysql.connect(**self.config)
            conn.close()
            return True
        except Exception as e:
            print(f"MySQL validation failed: {e}")
            return False
