"""
Change Data Capture (CDC) Monitor
Monitors database changes using PostgreSQL triggers and logical replication
"""
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Optional, Callable
from datetime import datetime
import json
import threading
import time


class CDCMonitor:
    """
    Monitors database changes using PostgreSQL's notification system
    """
    
    def __init__(self, database_url: str):
        """
        Initialize CDC monitor
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url)
        self.session_factory = sessionmaker(bind=self.engine)
        self.listeners = {}
        self.running = False
        self.monitor_thread = None
    
    def create_change_log_table(self):
        """
        Create a table to log all data changes
        """
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS data_change_log (
            change_id SERIAL PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            operation VARCHAR(10) NOT NULL,
            record_id INTEGER,
            old_data JSONB,
            new_data JSONB,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_name VARCHAR(100),
            change_metadata JSONB
        );
        
        CREATE INDEX IF NOT EXISTS idx_change_log_table 
        ON data_change_log(table_name);
        
        CREATE INDEX IF NOT EXISTS idx_change_log_time 
        ON data_change_log(changed_at);
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        
        print("[OK] Change log table created/verified")
    
    def create_trigger_function(self):
        """
        Create PostgreSQL trigger function to log changes
        """
        trigger_function_sql = """
        CREATE OR REPLACE FUNCTION log_table_changes()
        RETURNS TRIGGER AS $$
        DECLARE
            record_id_value INTEGER;
            old_data_json JSONB;
            new_data_json JSONB;
        BEGIN
            -- Handle different operations
            IF (TG_OP = 'DELETE') THEN
                record_id_value := OLD.patient_id;  -- Adjust based on your PK
                old_data_json := row_to_json(OLD)::JSONB;
                new_data_json := NULL;
            ELSIF (TG_OP = 'UPDATE') THEN
                record_id_value := NEW.patient_id;  -- Adjust based on your PK
                old_data_json := row_to_json(OLD)::JSONB;
                new_data_json := row_to_json(NEW)::JSONB;
            ELSIF (TG_OP = 'INSERT') THEN
                record_id_value := NEW.patient_id;  -- Adjust based on your PK
                old_data_json := NULL;
                new_data_json := row_to_json(NEW)::JSONB;
            END IF;
            
            -- Insert into change log
            INSERT INTO data_change_log (
                table_name, operation, record_id, old_data, new_data, user_name
            ) VALUES (
                TG_TABLE_NAME, TG_OP, record_id_value, 
                old_data_json, new_data_json, current_user
            );
            
            -- Notify listeners
            PERFORM pg_notify('data_changes', json_build_object(
                'table', TG_TABLE_NAME,
                'operation', TG_OP,
                'record_id', record_id_value,
                'timestamp', NOW()
            )::text);
            
            -- Return appropriate value
            IF (TG_OP = 'DELETE') THEN
                RETURN OLD;
            ELSE
                RETURN NEW;
            END IF;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(trigger_function_sql))
            conn.commit()
        
        print("[OK] Trigger function created/updated")
    
    def add_trigger_to_table(self, table_name: str):
        """
        Add change tracking trigger to a specific table
        
        Args:
            table_name: Name of the table to monitor
        """
        trigger_sql = f"""
        DROP TRIGGER IF EXISTS {table_name}_change_trigger ON {table_name};
        
        CREATE TRIGGER {table_name}_change_trigger
        AFTER INSERT OR UPDATE OR DELETE ON {table_name}
        FOR EACH ROW
        EXECUTE FUNCTION log_table_changes();
        """
        
        with self.engine.connect() as conn:
            conn.execute(text(trigger_sql))
            conn.commit()
        
        print(f"[OK] Trigger added to table: {table_name}")
    
    def setup_cdc_for_tables(self, table_names: List[str]):
        """
        Setup CDC monitoring for multiple tables
        
        Args:
            table_names: List of table names to monitor
        """
        print("\n" + "=" * 60)
        print("Setting up Change Data Capture")
        print("=" * 60)
        
        # Create infrastructure
        self.create_change_log_table()
        self.create_trigger_function()
        
        # Add triggers to tables
        for table_name in table_names:
            self.add_trigger_to_table(table_name)
        
        print(f"\n[OK] CDC setup complete for {len(table_names)} tables")
    
    def get_recent_changes(self, 
                          table_name: Optional[str] = None,
                          limit: int = 100) -> List[Dict]:
        """
        Get recent changes from the change log
        
        Args:
            table_name: Optional table name to filter
            limit: Maximum number of changes to return
            
        Returns:
            List of change records
        """
        query = """
        SELECT 
            change_id,
            table_name,
            operation,
            record_id,
            old_data,
            new_data,
            changed_at,
            user_name
        FROM data_change_log
        """
        
        if table_name:
            query += f" WHERE table_name = :table_name"
        
        query += " ORDER BY changed_at DESC LIMIT :limit"
        
        with self.engine.connect() as conn:
            if table_name:
                result = conn.execute(
                    text(query), 
                    {"table_name": table_name, "limit": limit}
                )
            else:
                result = conn.execute(text(query), {"limit": limit})
            
            changes = []
            for row in result:
                changes.append({
                    'change_id': row[0],
                    'table_name': row[1],
                    'operation': row[2],
                    'record_id': row[3],
                    'old_data': row[4],
                    'new_data': row[5],
                    'changed_at': row[6].isoformat() if row[6] else None,
                    'user_name': row[7]
                })
            
            return changes
    
    def get_change_statistics(self) -> Dict:
        """
        Get statistics about database changes
        
        Returns:
            Dictionary with change statistics
        """
        stats_query = """
        SELECT 
            table_name,
            operation,
            COUNT(*) as count
        FROM data_change_log
        GROUP BY table_name, operation
        ORDER BY table_name, operation
        """
        
        with self.engine.connect() as conn:
            result = conn.execute(text(stats_query))
            
            stats = {}
            for row in result:
                table = row[0]
                operation = row[1]
                count = row[2]
                
                if table not in stats:
                    stats[table] = {}
                stats[table][operation] = count
            
            return stats
    
    def register_change_listener(self, 
                                 table_name: str, 
                                 callback: Callable):
        """
        Register a callback function to be called on changes
        
        Args:
            table_name: Table to listen for changes
            callback: Function to call when change occurs
        """
        if table_name not in self.listeners:
            self.listeners[table_name] = []
        self.listeners[table_name].append(callback)
    
    def start_monitoring(self):
        """
        Start monitoring for real-time changes (placeholder)
        """
        print("\n[INFO] Real-time monitoring would start here")
        print("[INFO] In production, this would use pg_notify/LISTEN")
        print("[INFO] For now, use get_recent_changes() to poll for changes")


def setup_cdc(database_url: str, tables: List[str]):
    """
    Convenience function to setup CDC
    
    Args:
        database_url: Database connection URL
        tables: List of tables to monitor
    """
    monitor = CDCMonitor(database_url)
    monitor.setup_cdc_for_tables(tables)
    return monitor


if __name__ == "__main__":
    # Test CDC setup
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from common.config import settings
    
    # Tables to monitor
    tables_to_monitor = ['patients', 'encounters', 'lab_results', 'medications']
    
    print("Setting up Change Data Capture...")
    monitor = setup_cdc(settings.hospital_db_url, tables_to_monitor)
    
    print("\n" + "=" * 60)
    print("Testing CDC - Getting recent changes")
    print("=" * 60)
    
    changes = monitor.get_recent_changes(limit=10)
    print(f"\nRecent changes: {len(changes)}")
    
    if changes:
        for change in changes[:3]:  # Show first 3
            print(f"\n  Change ID: {change['change_id']}")
            print(f"  Table: {change['table_name']}")
            print(f"  Operation: {change['operation']}")
            print(f"  Time: {change['changed_at']}")
    else:
        print("  No changes recorded yet")
    
    print("\n[OK] CDC setup complete!")
