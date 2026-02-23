"""
Oracle CDC Adapter - Trigger-based with JSON CLOB
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cdc.base_adapter import CDCAdapter, ChangeEvent, OperationType
from typing import List, Optional

try:
    import cx_Oracle
    ORACLE_AVAILABLE = True
except ImportError:
    ORACLE_AVAILABLE = False


class OracleAdapter(CDCAdapter):
    """Oracle trigger-based CDC adapter"""
    
    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        if not ORACLE_AVAILABLE:
            raise ImportError("Oracle adapter requires: pip install cx_Oracle")
        
        # Parse: oracle://user:pass@host:port/service
        parts = connection_string.replace('oracle://', '').split('@')
        user_pass = parts[0].split(':')
        host_service = parts[1].split('/')
        host_port = host_service[0].split(':')
        
        self.config = {
            'user': user_pass[0],
            'password': user_pass[1] if len(user_pass) > 1 else '',
            'dsn': cx_Oracle.makedsn(
                host_port[0],
                int(host_port[1]) if len(host_port) > 1 else 1521,
                service_name=host_service[1] if len(host_service) > 1 else 'XEPDB1'
            )
        }
    
    def get_database_type(self) -> str:
        return "oracle"
    
    def _get_connection(self):
        return cx_Oracle.connect(**self.config)
    
    def setup_cdc(self, tables: List[str]) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create change log table
            cursor.execute("""
                BEGIN
                    EXECUTE IMMEDIATE 'DROP TABLE data_change_log';
                EXCEPTION WHEN OTHERS THEN NULL;
                END;
            """)
            
            cursor.execute("""
                CREATE TABLE data_change_log (
                    change_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                    table_name VARCHAR2(100) NOT NULL,
                    operation VARCHAR2(10) NOT NULL,
                    record_id NUMBER,
                    old_data CLOB CHECK (old_data IS JSON),
                    new_data CLOB CHECK (new_data IS JSON),
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("CREATE INDEX idx_change_table ON data_change_log(table_name)")
            
            for table in tables:
                table_upper = table.upper()
                pk_col = f'{table[:-1].upper()}_ID'
                
                # Drop existing triggers
                cursor.execute(f"""
                    BEGIN
                        EXECUTE IMMEDIATE 'DROP TRIGGER {table_upper}_CDC_TRG';
                    EXCEPTION WHEN OTHERS THEN NULL;
                    END;
                """)
                
                # Create compound trigger
                cursor.execute(f"""
                    CREATE OR REPLACE TRIGGER {table_upper}_CDC_TRG
                    FOR INSERT OR UPDATE OR DELETE ON {table_upper}
                    COMPOUND TRIGGER
                    v_op VARCHAR2(10);
                    v_id NUMBER;
                    v_old CLOB;
                    v_new CLOB;
                    
                    AFTER EACH ROW IS
                    BEGIN
                        IF INSERTING THEN
                            v_op := 'INSERT';
                            v_id := :NEW.{pk_col};
                            v_new := JSON_OBJECT('{pk_col}' VALUE :NEW.{pk_col});
                        ELSIF UPDATING THEN
                            v_op := 'UPDATE';
                            v_id := :NEW.{pk_col};
                            v_old := JSON_OBJECT('{pk_col}' VALUE :OLD.{pk_col});
                            v_new := JSON_OBJECT('{pk_col}' VALUE :NEW.{pk_col});
                        ELSIF DELETING THEN
                            v_op := 'DELETE';
                            v_id := :OLD.{pk_col};
                            v_old := JSON_OBJECT('{pk_col}' VALUE :OLD.{pk_col});
                        END IF;
                        
                        INSERT INTO data_change_log (table_name, operation, record_id, old_data, new_data)
                        VALUES ('{table}', v_op, v_id, v_old, v_new);
                    END AFTER EACH ROW;
                    END;
                """)
                
                print(f"  [OK] Oracle CDC trigger created for: {table}")
            
            conn.commit()
            conn.close()
            self.is_setup = True
            return True
        except Exception as e:
            print(f"Oracle CDC setup failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_changes(self, since_change_id=None, table_name=None, limit=100) -> List[ChangeEvent]:
        changes = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = "SELECT * FROM data_change_log WHERE 1=1"
            params = {}
            
            if since_change_id:
                query += " AND change_id > :since_id"
                params['since_id'] = since_change_id
            
            if table_name:
                query += " AND table_name = :table_name"
                params['table_name'] = table_name
            
            query += " ORDER BY change_id FETCH FIRST :limit ROWS ONLY"
            params['limit'] = limit
            
            cursor.execute(query, params)
            
            for row in cursor:
                changes.append(ChangeEvent(
                    change_id=int(row[0]),
                    table_name=row[1],
                    operation=OperationType[row[2]],
                    record_id=int(row[3]) if row[3] else None,
                    old_data=row[4].read() if row[4] else None,
                    new_data=row[5].read() if row[5] else None,
                    changed_at=row[6],
                    database_type='oracle'
                ))
            
            conn.close()
        except Exception as e:
            print(f"Error getting Oracle changes: {e}")
        
        return changes
    
    def get_latest_change_id(self) -> Optional[int]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(change_id) FROM data_change_log")
            result = cursor.fetchone()
            conn.close()
            return int(result[0]) if result and result[0] else None
        except:
            return None
    
    def validate_connection(self) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUAL")
            conn.close()
            return True
        except:
            return False
