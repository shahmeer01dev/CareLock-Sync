"""
Automatic Real-Time CDC Sync Daemon
Monitors all databases and automatically synchronizes changes to FHIR central database

NO HUMAN INTERACTION REQUIRED - Runs 24/7 in background
"""
import sys
import os
import time
import threading
from datetime import datetime
from typing import Dict, List
import json

sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\etl')
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend\cdc')

from incremental_sync import IncrementalSync
from adapter_factory import CDCAdapterFactory
from common.config import settings


class AutoSyncDaemon:
    """
    Automatic synchronization daemon - monitors databases and syncs automatically
    
    Features:
    - Real-time monitoring (configurable interval, default 5 seconds)
    - Multi-database support (PostgreSQL, MySQL, MongoDB, Oracle, SQL Server)
    - Automatic watermark persistence
    - Zero human interaction
    - Error recovery
    - Statistics tracking
    """
    
    STATE_FILE = r'C:\Projects\CareLock-Sync\backend\autosync_state.json'
    
    def __init__(self, 
                 tenant_id: int = 1,
                 poll_interval: int = 5,  # Check for changes every 5 seconds
                 databases: List[str] = None):
        """
        Initialize auto-sync daemon
        
        Args:
            tenant_id: Hospital tenant ID
            poll_interval: Seconds between checks (default: 5 = real-time)
            databases: List of database connection strings to monitor
        """
        self.tenant_id = tenant_id
        self.poll_interval = poll_interval
        
        # Default to configured database
        if databases is None:
            self.databases = [settings.hospital_db_url]
        else:
            self.databases = databases
        
        self.is_running = False
        self.threads = []
        
        # Load persistent state
        self.state = self._load_state()
        
        # Statistics
        self.stats = {
            'daemon_started': None,
            'total_sync_cycles': 0,
            'total_changes_synced': 0,
            'total_errors': 0,
            'databases_monitored': len(self.databases),
            'last_sync_time': None,
            'uptime_seconds': 0
        }
    
    def _load_state(self) -> Dict:
        """Load persistent watermarks for each database"""
        if os.path.exists(self.STATE_FILE):
            try:
                with open(self.STATE_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Could not load state: {e}")
        
        # Initialize state for each database
        return {
            'watermarks': {db: 0 for db in self.databases},
            'last_sync': {}
        }
    
    def _save_state(self):
        """Persist watermarks to disk"""
        try:
            with open(self.STATE_FILE, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Could not save state: {e}")
    
    def _monitor_database(self, db_conn_string: str):
        """
        Monitor a single database for changes and auto-sync
        Runs in separate thread for each database
        """
        db_type = CDCAdapterFactory.detect_database_type(db_conn_string)
        print(f"[{db_type.upper()}] Starting real-time monitor...")
        
        sync = IncrementalSync(tenant_id=self.tenant_id)
        
        while self.is_running:
            try:
                # Get current watermark
                current_watermark = self.state['watermarks'].get(db_conn_string, 0)
                
                # Check for changes
                stats = sync.sync_incremental(last_sync_id=current_watermark)
                
                # Update watermark if changes were processed
                if stats.get('last_change_id') and stats['last_change_id'] > current_watermark:
                    self.state['watermarks'][db_conn_string] = stats['last_change_id']
                    self.state['last_sync'][db_conn_string] = datetime.now().isoformat()
                    self._save_state()
                    
                    # Update stats
                    self.stats['total_sync_cycles'] += 1
                    self.stats['total_changes_synced'] += stats.get('synced', 0)
                    self.stats['last_sync_time'] = datetime.now().isoformat()
                    
                    if stats.get('total_changes', 0) > 0:
                        print(f"[{db_type.upper()}] ✓ Synced {stats['synced']} changes "
                              f"(watermark: {current_watermark} → {stats['last_change_id']})")
                
                # Wait before next check
                time.sleep(self.poll_interval)
                
            except Exception as e:
                self.stats['total_errors'] += 1
                print(f"[{db_type.upper()}] ✗ Error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(self.poll_interval * 2)  # Back off on errors
    
    def start(self):
        """Start the auto-sync daemon"""
        if self.is_running:
            print("[DAEMON] Already running")
            return
        
        self.is_running = True
        self.stats['daemon_started'] = datetime.now().isoformat()
        
        print("=" * 80)
        print("AUTOMATIC REAL-TIME CDC SYNC DAEMON")
        print("=" * 80)
        print(f"Tenant ID         : {self.tenant_id}")
        print(f"Poll Interval     : {self.poll_interval} seconds (real-time)")
        print(f"Databases Monitored: {len(self.databases)}")
        for db in self.databases:
            db_type = CDCAdapterFactory.detect_database_type(db)
            watermark = self.state['watermarks'].get(db, 0)
            print(f"  - {db_type.upper():<12s}: watermark={watermark}")
        print(f"State File        : {self.STATE_FILE}")
        print(f"Started At        : {self.stats['daemon_started']}")
        print("=" * 80)
        print()
        print("[DAEMON RUNNING] - Changes will sync automatically (NO HUMAN INTERACTION)")
        print("   Press Ctrl+C to stop...")
        print()
        
        # Start monitoring thread for each database
        for db_conn in self.databases:
            thread = threading.Thread(
                target=self._monitor_database,
                args=(db_conn,),
                daemon=True,
                name=f"Monitor-{CDCAdapterFactory.detect_database_type(db_conn)}"
            )
            thread.start()
            self.threads.append(thread)
        
        # Statistics reporting thread
        def report_stats():
            while self.is_running:
                time.sleep(60)  # Report every minute
                if self.stats['total_changes_synced'] > 0:
                    uptime = (datetime.now() - 
                             datetime.fromisoformat(self.stats['daemon_started'])).total_seconds()
                    self.stats['uptime_seconds'] = int(uptime)
                    
                    print(f"\n[STATS] Uptime: {int(uptime/60)}min | "
                          f"Synced: {self.stats['total_changes_synced']} changes | "
                          f"Cycles: {self.stats['total_sync_cycles']} | "
                          f"Errors: {self.stats['total_errors']}\n")
        
        stats_thread = threading.Thread(target=report_stats, daemon=True)
        stats_thread.start()
        self.threads.append(stats_thread)
    
    def stop(self):
        """Stop the daemon"""
        if not self.is_running:
            return
        
        print("\n\n[DAEMON] Stopping...")
        self.is_running = False
        
        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=2)
        
        # Save final state
        self._save_state()
        
        # Final statistics
        print("\n" + "=" * 80)
        print("DAEMON STOPPED - Final Statistics")
        print("=" * 80)
        print(f"Total Runtime     : {self.stats['uptime_seconds']} seconds")
        print(f"Sync Cycles       : {self.stats['total_sync_cycles']}")
        print(f"Changes Synced    : {self.stats['total_changes_synced']}")
        print(f"Errors            : {self.stats['total_errors']}")
        print(f"Databases         : {self.stats['databases_monitored']}")
        
        print(f"\nFinal Watermarks:")
        for db, watermark in self.state['watermarks'].items():
            db_type = CDCAdapterFactory.detect_database_type(db)
            print(f"  {db_type.upper():<12s}: {watermark}")
        
        print("=" * 80)
        print(f"State saved to: {self.STATE_FILE}")
        print("=" * 80)
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        return {
            **self.stats,
            'is_running': self.is_running,
            'poll_interval': self.poll_interval,
            'watermarks': self.state['watermarks']
        }


# ══════════════════════════════════════════════════════════════════════════
# Main Entry Point
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Automatic Real-Time CDC Sync Daemon - NO HUMAN INTERACTION REQUIRED'
    )
    parser.add_argument('--interval', type=int, default=5,
                       help='Poll interval in seconds (default: 5 = real-time)')
    parser.add_argument('--databases', nargs='+',
                       help='Database connection strings to monitor')
    parser.add_argument('--reset', action='store_true',
                       help='Reset all watermarks to 0')
    args = parser.parse_args()
    
    # Handle reset
    if args.reset:
        state_file = r'C:\Projects\CareLock-Sync\backend\autosync_state.json'
        if os.path.exists(state_file):
            os.remove(state_file)
            print(f"[OK] Reset watermarks: {state_file}")
        else:
            print("[INFO] No state file to reset")
        sys.exit(0)
    
    # Start daemon
    daemon = AutoSyncDaemon(
        tenant_id=1,
        poll_interval=args.interval,
        databases=args.databases
    )
    
    try:
        daemon.start()
        
        # Keep main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        daemon.stop()
