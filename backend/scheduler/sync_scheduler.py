"""
Automatic Sync Scheduler
Runs periodic syncs in the background
"""
import schedule
import time
import threading
from datetime import datetime
from typing import Optional
import sys
import os

# Fix imports properly
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

# Add ETL path
etl_path = os.path.join(backend_dir, 'etl')
sys.path.insert(0, etl_path)

from incremental_sync import IncrementalSync
from common.database import hospital_db_session
from sqlalchemy import text


class SyncScheduler:
    """
    Automatic sync scheduler that runs incremental syncs periodically
    """
    
    def __init__(self, tenant_id: int = 1, interval_seconds: int = 60):
        """
        Initialize sync scheduler
        
        Args:
            tenant_id: Hospital tenant ID
            interval_seconds: Seconds between syncs (default: 60 = 1 minute)
        """
        self.tenant_id = tenant_id
        self.interval_seconds = interval_seconds
        self.sync_service = IncrementalSync(tenant_id)
        self.last_sync_id = self._get_last_processed_change_id()
        self.is_running = False
        self.scheduler_thread = None
        
        # Statistics
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'total_changes_synced': 0,
            'last_run_time': None,
            'last_error': None
        }
    
    def _get_last_processed_change_id(self) -> Optional[int]:
        """Get the last change ID that was processed"""
        try:
            with hospital_db_session() as db:
                result = db.execute(text("""
                    SELECT MAX(change_id) FROM data_change_log
                """))
                max_id = result.scalar()
                return max_id if max_id else 0
        except Exception as e:
            print(f"Error getting last change ID: {e}")
            return 0
    
    def _run_sync(self):
        """Run incremental sync job"""
        try:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Running automatic sync...")
            
            # Run incremental sync
            stats = self.sync_service.sync_incremental(last_sync_id=self.last_sync_id)
            
            # Update last sync ID
            if 'last_change_id' in stats:
                self.last_sync_id = stats['last_change_id']
            
            # Update statistics
            self.stats['total_runs'] += 1
            self.stats['last_run_time'] = datetime.now().isoformat()
            
            if stats.get('total_changes', 0) > 0:
                self.stats['successful_runs'] += 1
                self.stats['total_changes_synced'] += stats.get('synced', 0)
                print(f"  ✓ Synced {stats.get('synced', 0)} changes")
            else:
                print(f"  • No new changes")
            
            self.stats['last_error'] = None
            
        except Exception as e:
            self.stats['failed_runs'] += 1
            self.stats['last_error'] = str(e)
            print(f"  ✗ Sync failed: {e}")
    
    def start(self):
        """Start the automatic sync scheduler"""
        if self.is_running:
            print("Scheduler already running")
            return
        
        self.is_running = True
        
        # Schedule the sync job
        schedule.every(self.interval_seconds).seconds.do(self._run_sync)
        
        print("=" * 70)
        print("Automatic Sync Scheduler Started")
        print("=" * 70)
        print(f"Tenant ID: {self.tenant_id}")
        print(f"Sync Interval: {self.interval_seconds} seconds")
        print(f"Last Change ID: {self.last_sync_id}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        # Run in background thread
        def run_scheduler():
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        # Initial sync
        self._run_sync()
    
    def stop(self):
        """Stop the scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        schedule.clear()
        
        print("\n" + "=" * 70)
        print("Scheduler Stopped")
        print("=" * 70)
        print(f"Total Runs: {self.stats['total_runs']}")
        print(f"Changes Synced: {self.stats['total_changes_synced']}")
        print("=" * 70)
    
    def get_stats(self):
        """Get statistics"""
        return {
            **self.stats,
            'is_running': self.is_running,
            'interval_seconds': self.interval_seconds,
            'last_sync_id': self.last_sync_id
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Automatic Sync Scheduler')
    parser.add_argument('--interval', type=int, default=60,
                       help='Sync interval in seconds (default: 60)')
    args = parser.parse_args()
    
    scheduler = SyncScheduler(tenant_id=1, interval_seconds=args.interval)
    
    try:
        scheduler.start()
        print("\nPress Ctrl+C to stop...\n")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nStopping...")
        scheduler.stop()
