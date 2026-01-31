"""Test incremental sync with last change ID"""
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from etl.incremental_sync import IncrementalSync

sync = IncrementalSync(tenant_id=1)

# Sync only changes after change_id 2
print("Syncing changes after ID 2...")
stats = sync.sync_incremental(last_sync_id=2)
