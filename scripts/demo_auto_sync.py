"""
Demo: Automatic Sync in Action
Shows the scheduler working with a short interval
"""
import sys
sys.path.insert(0, r'C:\Projects\CareLock-Sync\backend')

from scheduler.sync_scheduler import SyncScheduler
import time

print("=" * 70)
print("Automatic Sync Scheduler Demo")
print("=" * 70)
print("\nThis demonstrates automatic syncing every 30 seconds")
print("The scheduler will detect and sync changes automatically\n")

# Create scheduler with 30-second interval
scheduler = SyncScheduler(tenant_id=1, interval_seconds=30)

# Start the scheduler
scheduler.start()

print("\n** Make a change in another terminal to see automatic sync **")
print("Example:")
print('docker exec carelock-hospital-db psql -U hospital_user -d hospital_db -c "UPDATE patients SET email=\'auto@test.com\' WHERE patient_id=15;"')
print("\nRunning for 2 minutes...\n")

try:
    # Run for 2 minutes
    for i in range(120):
        time.sleep(1)
        if i % 30 == 0 and i > 0:
            stats = scheduler.get_stats()
            print(f"\n[Stats] Runs: {stats['total_runs']}, Changes: {stats['total_changes_synced']}")
    
    # Stop scheduler
    scheduler.stop()
    
    # Show final stats
    print("\n" + "=" * 70)
    print("Final Statistics:")
    stats = scheduler.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
except KeyboardInterrupt:
    print("\n\nStopping scheduler...")
    scheduler.stop()
