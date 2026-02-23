"""
SQL Server CDC Adapter - Trigger-based with JSON (FIXED VERSION)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cdc.base_adapter import CDCAdapter, ChangeEvent, OperationType
from typing import List, Optional
import json

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
        
        # Parse: sqlserver://user:pass@host:port/database
        parts = connection_string.replace('sqlserver://', '').split('@')
        user_pass = parts[0].split(':')
        host_db = parts[1].split('/')
        host_port = host_db[0].split(':')
        
        # Try ODBC Driver 18 first, then 17
        try:
            drivers = pyodbc.drivers()
            if 'ODBC Driver 18 for SQL Server' in drivers:
                driver = '{ODBC Driver 18 for SQL Server}'
            elif 'ODBC Driver 17 for SQL Server' in drivers:
                driver = '{ODBC Driver 17 for SQL Server}'
            else:
                driver = '{SQL Server}'
        except:
            driver = '{ODBC Driver 17 for SQL Server}'
        
        server = f"{host_port[0]},{host_port[1] if len(host_port) > 1 else '1433'}"
        database = host_db[1] if len(host_db) > 1 else 'hospital_db'
        
        self.conn_str = (
            f'DRIVER={driver};SERVER={server};DATABASE={database};'
            f'UID={user_pass[0]};PWD={user_pass[1] if len(user_pass) > 1 else ""};'
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
