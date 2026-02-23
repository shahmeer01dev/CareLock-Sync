"""
SQL Server CDC Adapter - FULLY FIXED VERSION
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cdc.base_adapter import CDCAdapter, ChangeEvent, OperationType
from typing import List, Optional
from urllib.parse import urlparse

try:
    import pyodbc
    SQLSERVER_AVAILABLE = True
except ImportError:
    SQLSERVER_AVAILABLE = False


class SQLServerAdapter(CDCAdapter):
    """SQL Server trigger-based CDC adapter"""
    
    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        if not SQLSERVER_AVAILABLE:
            raise ImportError("SQL Server adapter requires: pip install pyodbc")
        
        # Parse using urlparse to handle special characters in password
        # Format: sqlserver://user:pass@host:port/database
        parsed = urlparse(connection_string)
        
        username = parsed.username or 'sa'
        password = parsed.password or ''
        hostname = parsed.hostname or 'localhost'
        port = parsed.port or 1433
        database = parsed.path.lstrip('/') if parsed.path else 'hospital_db'
        
        # Auto-detect best ODBC driver
        try:
            available_drivers = pyodbc.drivers()
            if 'ODBC Driver 18 for SQL Server' in available_drivers:
                driver = '{ODBC Driver 18 for SQL Server}'
            elif 'ODBC Driver 17 for SQL Server' in available_drivers:
                driver = '{ODBC Driver 17 for SQL Server}'
            else:
                driver = '{SQL Server}'
        except:
            driver = '{ODBC Driver 17 for SQL Server}'
        
        # Build connection string with TrustServerCertificate
        self.conn_str = (
            f'DRIVER={driver};'
            f'SERVER={hostname},{port};'
            f'DATABASE={database};'
            f'UID={username};'
            f'PWD={password};'
            f'TrustServerCertificate=yes'
        )
        self.database = database
    
    def get_database_type(self) -> str:
        return "sqlserver"
    
    def _get_connection(self):
        return pyodbc.connect(self.conn_str)
    
    def validate_connection(self) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            print(f"SQL Server validation failed: {e}")
            return False
    
    def setup_cdc(self, tables: List[str]) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create change log table
            cursor.execute("""
                IF OBJECT_ID('dbo.data_change_log', 'U') IS NOT NULL
                    DROP TABLE dbo.data_change_log
            """)
            
            cursor.execute("""
                CREATE TABLE data_change_log (
                    change_id BIGINT IDENTITY(1,1) PRIMARY KEY,
                    table_name NVARCHAR(100) NOT NULL,
                    operation NVARCHAR(10) NOT NULL,
                    record_id INT,
                    old_data NVARCHAR(MAX),
                    new_data NVARCHAR(MAX),
                    changed_at DATETIME2 DEFAULT SYSDATETIME()
                )
            """)
            
            cursor.execute("CREATE INDEX idx_change_table ON data_change_log(table_name)")
            
            for table in tables:
                # Get primary key
                cursor.execute(f"""
                    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                    WHERE OBJECTPROPERTY(OBJECT_ID(CONSTRAINT_SCHEMA + '.' + CONSTRAINT_NAME), 'IsPrimaryKey') = 1
                    AND TABLE_NAME = '{table}'
                """)
                pk_result = cursor.fetchone()
                pk_col = pk_result[0] if pk_result else f'{table[:-1]}_id'
                
                # Drop old triggers
                for op in ['insert', 'update', 'delete']:
                    cursor.execute(f"""
                        IF OBJECT_ID('dbo.{table}_{op}_trg', 'TR') IS NOT NULL
                            DROP TRIGGER dbo.{table}_{op}_trg
                    """)
                
                # CREATE triggers
                cursor.execute(f"""
                    CREATE TRIGGER {table}_insert_trg ON {table} AFTER INSERT
                    AS BEGIN
                        SET NOCOUNT ON;
                        INSERT INTO data_change_log (table_name, operation, record_id, new_data)
                        SELECT '{table}', 'INSERT', i.{pk_col},
                               (SELECT * FROM inserted i2 WHERE i2.{pk_col} = i.{pk_col} FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
                        FROM inserted i;
                    END
                """)
                
                cursor.execute(f"""
                    CREATE TRIGGER {table}_update_trg ON {table} AFTER UPDATE
                    AS BEGIN
                        SET NOCOUNT ON;
                        INSERT INTO data_change_log (table_name, operation, record_id, old_data, new_data)
                        SELECT '{table}', 'UPDATE', i.{pk_col},
                               (SELECT * FROM deleted d WHERE d.{pk_col} = i.{pk_col} FOR JSON PATH, WITHOUT_ARRAY_WRAPPER),
                               (SELECT * FROM inserted i2 WHERE i2.{pk_col} = i.{pk_col} FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
                        FROM inserted i;
                    END
                """)
                
                cursor.execute(f"""
                    CREATE TRIGGER {table}_delete_trg ON {table} AFTER DELETE
                    AS BEGIN
                        SET NOCOUNT ON;
                        INSERT INTO data_change_log (table_name, operation, record_id, old_data)
                        SELECT '{table}', 'DELETE', d.{pk_col},
                               (SELECT * FROM deleted d2 WHERE d2.{pk_col} = d.{pk_col} FOR JSON PATH, WITHOUT_ARRAY_WRAPPER)
                        FROM deleted d;
                    END
                """)
                
                print(f"  [OK] SQL Server CDC triggers created for: {table}")
            
            conn.commit()
            conn.close()
            self.is_setup = True
            return True
        except Exception as e:
            print(f"SQL Server CDC setup failed: {e}")
            return False
    
    def get_changes(self, since_change_id=None, table_name=None, limit=100) -> List[ChangeEvent]:
        changes = []
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            query = f"SELECT TOP ({limit}) * FROM data_change_log WHERE 1=1"
            params = []
            
            if since_change_id:
                query = query.replace("WHERE 1=1", "WHERE change_id > ?")
                params.append(since_change_id)
            
            if table_name:
                query += " AND table_name = ?"
                params.append(table_name)
            
            query += " ORDER BY change_id"
            
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            
            for row in cursor:
                row_dict = dict(zip(columns, row))
                changes.append(ChangeEvent(
                    change_id=row_dict['change_id'],
                    table_name=row_dict['table_name'],
                    operation=OperationType[row_dict['operation']],
                    record_id=row_dict['record_id'],
                    old_data=row_dict['old_data'],
                    new_data=row_dict['new_data'],
                    changed_at=row_dict['changed_at'],
                    database_type='sqlserver'
                ))
            
            conn.close()
        except Exception as e:
            print(f"Error getting SQL Server changes: {e}")
        
        return changes
    
    def get_latest_change_id(self) -> Optional[int]:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(change_id) FROM data_change_log")
            result = cursor.fetchone()
            conn.close()
            return result[0] if result and result[0] else None
        except:
            return None
