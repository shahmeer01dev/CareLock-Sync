"""
API routes for sync operations
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import sys
import os

# Fix imports
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
backend_dir = os.path.dirname(api_dir)
sys.path.insert(0, backend_dir)

# Import ETL modules
etl_path = os.path.join(backend_dir, 'etl')
sys.path.insert(0, etl_path)

from pipeline import ETLPipeline
from incremental_sync import IncrementalSync

router = APIRouter(
    prefix="/api/v1/sync",
    tags=["sync"]
)

# Pydantic models
class SyncRequest(BaseModel):
    """Sync request model"""
    tenant_id: int = 1
    limit: Optional[int] = None
    resource_types: Optional[list] = None  # ['patients', 'encounters']


class IncrementalSyncRequest(BaseModel):
    """Incremental sync request model"""
    tenant_id: int = 1
    last_sync_id: Optional[int] = None


class SyncResponse(BaseModel):
    """Sync response model"""
    status: str
    message: str
    sync_id: Optional[str] = None
    started_at: str
    stats: Optional[Dict[str, Any]] = None


class SyncStatus(BaseModel):
    """Sync status model"""
    is_syncing: bool
    last_sync_time: Optional[str] = None
    last_sync_stats: Optional[Dict[str, Any]] = None
    total_syncs: int


# Global state (in production, use Redis or database)
sync_state = {
    'is_syncing': False,
    'last_sync_time': None,
    'last_sync_stats': None,
    'total_syncs': 0,
    'sync_history': []
}


@router.post("/full", response_model=SyncResponse)
async def trigger_full_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks
):
    """
    Trigger a full synchronization
    
    Syncs all data from hospital database to FHIR shared database
    """
    if sync_state['is_syncing']:
        raise HTTPException(status_code=409, detail="Sync already in progress")
    
    try:
        sync_state['is_syncing'] = True
        
        # Create sync ID
        sync_id = f"full_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.utcnow().isoformat()
        
        # Run sync
        pipeline = ETLPipeline(tenant_id=request.tenant_id)
        stats = pipeline.sync_all(limit=request.limit)
        
        # Update state
        sync_state['is_syncing'] = False
        sync_state['last_sync_time'] = started_at
        sync_state['last_sync_stats'] = stats
        sync_state['total_syncs'] += 1
        sync_state['sync_history'].append({
            'sync_id': sync_id,
            'type': 'full',
            'started_at': started_at,
            'completed_at': datetime.utcnow().isoformat(),
            'stats': stats
        })
        
        # Keep only last 10 syncs in history
        if len(sync_state['sync_history']) > 10:
            sync_state['sync_history'] = sync_state['sync_history'][-10:]
        
        return {
            "status": "completed",
            "message": "Full sync completed successfully",
            "sync_id": sync_id,
            "started_at": started_at,
            "stats": stats
        }
        
    except Exception as e:
        sync_state['is_syncing'] = False
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.post("/incremental", response_model=SyncResponse)
async def trigger_incremental_sync(request: IncrementalSyncRequest):
    """
    Trigger an incremental synchronization
    
    Syncs only changed records based on CDC change log
    """
    if sync_state['is_syncing']:
        raise HTTPException(status_code=409, detail="Sync already in progress")
    
    try:
        sync_state['is_syncing'] = True
        
        # Create sync ID
        sync_id = f"incremental_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.utcnow().isoformat()
        
        # Run incremental sync
        sync_service = IncrementalSync(tenant_id=request.tenant_id)
        stats = sync_service.sync_incremental(last_sync_id=request.last_sync_id)
        
        # Update state
        sync_state['is_syncing'] = False
        sync_state['last_sync_time'] = started_at
        sync_state['last_sync_stats'] = stats
        sync_state['total_syncs'] += 1
        sync_state['sync_history'].append({
            'sync_id': sync_id,
            'type': 'incremental',
            'started_at': started_at,
            'completed_at': datetime.utcnow().isoformat(),
            'stats': stats
        })
        
        # Keep only last 10 syncs
        if len(sync_state['sync_history']) > 10:
            sync_state['sync_history'] = sync_state['sync_history'][-10:]
        
        return {
            "status": "completed",
            "message": f"Incremental sync completed. Processed {stats.get('total_changes', 0)} changes",
            "sync_id": sync_id,
            "started_at": started_at,
            "stats": stats
        }
        
    except Exception as e:
        sync_state['is_syncing'] = False
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/status", response_model=SyncStatus)
async def get_sync_status():
    """
    Get current sync status
    """
    return {
        "is_syncing": sync_state['is_syncing'],
        "last_sync_time": sync_state['last_sync_time'],
        "last_sync_stats": sync_state['last_sync_stats'],
        "total_syncs": sync_state['total_syncs']
    }


@router.get("/history")
async def get_sync_history(limit: int = 10):
    """
    Get sync history
    
    Returns list of recent sync operations
    """
    history = sync_state['sync_history'][-limit:]
    return {
        "total": len(sync_state['sync_history']),
        "limit": limit,
        "history": history
    }


@router.get("/statistics")
async def get_sync_statistics():
    """
    Get detailed sync statistics from shared database
    """
    try:
        from common.database import shared_db_session
        from sqlalchemy import text
        
        with shared_db_session() as db:
            # Get counts
            patient_count = db.execute(text("SELECT COUNT(*) FROM fhir_patient")).scalar()
            encounter_count = db.execute(text("SELECT COUNT(*) FROM fhir_encounter")).scalar()
            observation_count = db.execute(text("SELECT COUNT(*) FROM fhir_observation")).scalar()
            medication_count = db.execute(text("SELECT COUNT(*) FROM fhir_medication_request")).scalar()
            
            # Get tenant info
            tenant_query = text("""
                SELECT hospital_name, hospital_code, last_sync_date
                FROM hospital_tenants
                WHERE tenant_id = 1
            """)
            tenant = db.execute(tenant_query).fetchone()
            
            return {
                "tenant": {
                    "id": 1,
                    "name": tenant[0] if tenant else None,
                    "code": tenant[1] if tenant else None,
                    "last_sync": tenant[2].isoformat() if tenant and tenant[2] else None
                },
                "fhir_resources": {
                    "patients": patient_count or 0,
                    "encounters": encounter_count or 0,
                    "observations": observation_count or 0,
                    "medications": medication_count or 0,
                    "total": (patient_count or 0) + (encounter_count or 0) + 
                            (observation_count or 0) + (medication_count or 0)
                },
                "sync_state": {
                    "is_syncing": sync_state['is_syncing'],
                    "total_syncs": sync_state['total_syncs'],
                    "last_sync_time": sync_state['last_sync_time']
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.delete("/reset")
async def reset_sync_state():
    """
    Reset sync state (for testing/debugging)
    """
    sync_state['is_syncing'] = False
    sync_state['last_sync_time'] = None
    sync_state['last_sync_stats'] = None
    sync_state['total_syncs'] = 0
    sync_state['sync_history'] = []
    
    return {
        "status": "success",
        "message": "Sync state reset successfully"
    }
