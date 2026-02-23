"""
API routes for sync operations — Sprint 3: Auth wired
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import sys, os

current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir     = os.path.dirname(current_dir)
backend_dir = os.path.dirname(api_dir)
sys.path.insert(0, backend_dir)

etl_path = os.path.join(backend_dir, 'etl')
sys.path.insert(0, etl_path)

from pipeline          import ETLPipeline
from incremental_sync  import IncrementalSync
from common.database   import shared_db_session
from common.auth       import require_auth, require_admin, require_write, AuthContext
from sqlalchemy        import text

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])

# ── Pydantic models ──────────────────────────────────────────────────────────
class SyncRequest(BaseModel):
    tenant_id: int = 1
    limit: Optional[int] = None
    resource_types: Optional[list] = None

class IncrementalSyncRequest(BaseModel):
    tenant_id: int = 1
    last_sync_id: Optional[int] = None

class SyncResponse(BaseModel):
    status: str
    message: str
    sync_id: Optional[str] = None
    started_at: str
    stats: Optional[Dict[str, Any]] = None
    triggered_by: Optional[str] = None

class SyncStatus(BaseModel):
    is_syncing: bool
    last_sync_time: Optional[str] = None
    last_sync_stats: Optional[Dict[str, Any]] = None
    total_syncs: int

sync_state = {
    'is_syncing': False, 'last_sync_time': None,
    'last_sync_stats': None, 'total_syncs': 0, 'sync_history': []
}

# ── helpers ──────────────────────────────────────────────────────────────────
def _resolve_tenant(request_tenant: int, auth: AuthContext) -> int:
    """Return tenant to sync. Raise 403 if hospital key requests a different tenant."""
    if auth.role == "hospital":
        if request_tenant != auth.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your key is scoped to tenant {auth.tenant_id}, "
                       f"cannot sync tenant {request_tenant}"
            )
        return auth.tenant_id
    return request_tenant

def _append_history(sync_id, stype, started_at, stats):
    sync_state['sync_history'].append({
        'sync_id': sync_id, 'type': stype,
        'started_at': started_at,
        'completed_at': datetime.utcnow().isoformat(),
        'stats': stats
    })
    if len(sync_state['sync_history']) > 10:
        sync_state['sync_history'] = sync_state['sync_history'][-10:]

# ── Full sync ────────────────────────────────────────────────────────────────
@router.post("/full", response_model=SyncResponse)
async def trigger_full_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    auth: AuthContext = Depends(require_write)          # ← auth required
):
    if sync_state['is_syncing']:
        raise HTTPException(409, "Sync already in progress")
    tenant_id = _resolve_tenant(request.tenant_id, auth)
    auth.assert_tenant(tenant_id)
    try:
        sync_state['is_syncing'] = True
        sync_id    = f"full_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.utcnow().isoformat()
        stats = ETLPipeline(tenant_id=tenant_id).sync_all(limit=request.limit)
        sync_state.update(is_syncing=False, last_sync_time=started_at,
                          last_sync_stats=stats, total_syncs=sync_state['total_syncs']+1)
        _append_history(sync_id, 'full', started_at, stats)
        return {"status": "completed", "message": "Full sync completed",
                "sync_id": sync_id, "started_at": started_at,
                "stats": stats, "triggered_by": auth.api_key_id}
    except Exception as e:
        sync_state['is_syncing'] = False
        raise HTTPException(500, f"Sync failed: {e}")

# ── Incremental sync ─────────────────────────────────────────────────────────
@router.post("/incremental", response_model=SyncResponse)
async def trigger_incremental_sync(
    request: IncrementalSyncRequest,
    auth: AuthContext = Depends(require_write)          # ← auth required
):
    if sync_state['is_syncing']:
        raise HTTPException(409, "Sync already in progress")
    tenant_id = _resolve_tenant(request.tenant_id, auth)
    auth.assert_tenant(tenant_id)
    try:
        sync_state['is_syncing'] = True
        sync_id    = f"inc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        started_at = datetime.utcnow().isoformat()
        stats = IncrementalSync(tenant_id=tenant_id).sync_incremental(request.last_sync_id)
        sync_state.update(is_syncing=False, last_sync_time=started_at,
                          last_sync_stats=stats, total_syncs=sync_state['total_syncs']+1)
        _append_history(sync_id, 'incremental', started_at, stats)
        return {"status": "completed",
                "message": f"Incremental sync done. {stats.get('total_changes',0)} changes",
                "sync_id": sync_id, "started_at": started_at,
                "stats": stats, "triggered_by": auth.api_key_id}
    except Exception as e:
        sync_state['is_syncing'] = False
        raise HTTPException(500, f"Sync failed: {e}")

# ── Read-only endpoints ───────────────────────────────────────────────────────
@router.get("/status", response_model=SyncStatus)
async def get_sync_status(auth: AuthContext = Depends(require_auth)):
    return {"is_syncing": sync_state['is_syncing'],
            "last_sync_time": sync_state['last_sync_time'],
            "last_sync_stats": sync_state['last_sync_stats'],
            "total_syncs": sync_state['total_syncs']}

@router.get("/history")
async def get_sync_history(limit: int = 10, auth: AuthContext = Depends(require_auth)):
    return {"total": len(sync_state['sync_history']),
            "limit": limit, "history": sync_state['sync_history'][-limit:]}

@router.get("/statistics")
async def get_sync_statistics(auth: AuthContext = Depends(require_auth)):
    try:
        with shared_db_session() as db:
            if auth.role == "hospital":
                db.execute(text("SET app.tenant_id = :t"), {"t": str(auth.tenant_id)})
            counts = {
                t: db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                for t in ("fhir_patient","fhir_encounter","fhir_observation","fhir_medication_request")
            }
            tenant = db.execute(text(
                "SELECT hospital_name, hospital_code FROM hospital_tenants WHERE tenant_id=:t"
            ), {"t": auth.tenant_id or 1}).fetchone()
        return {"tenant": {"name": tenant[0] if tenant else None,
                           "code": tenant[1] if tenant else None},
                "fhir_resources": {**counts,
                    "total": sum(v or 0 for v in counts.values())},
                "sync_state": {"is_syncing": sync_state['is_syncing'],
                               "total_syncs": sync_state['total_syncs'],
                               "last_sync_time": sync_state['last_sync_time']}}
    except Exception as e:
        raise HTTPException(500, str(e))

# ── Admin-only ────────────────────────────────────────────────────────────────
@router.delete("/reset")
async def reset_sync_state(auth: AuthContext = Depends(require_admin)):
    sync_state.update(is_syncing=False, last_sync_time=None,
                      last_sync_stats=None, total_syncs=0, sync_history=[])
    return {"status": "success", "message": "Sync state reset", "by": auth.api_key_id}

# ── Observability ─────────────────────────────────────────────────────────────
@router.get("/health")
async def sync_health(auth: AuthContext = Depends(require_auth)):
    with shared_db_session() as db:
        rows = db.execute(text("SELECT * FROM v_cdc_lag")).fetchall()
    return {"cdc_lag": [dict(r._mapping) for r in rows],
            "checked_at": datetime.utcnow().isoformat()}

@router.get("/quality")
async def data_quality(auth: AuthContext = Depends(require_auth)):
    with shared_db_session() as db:
        rows = db.execute(text("SELECT * FROM v_tenant_health")).fetchall()
    return {"tenants": [dict(r._mapping) for r in rows],
            "checked_at": datetime.utcnow().isoformat()}

@router.get("/partitions")
async def partition_health(auth: AuthContext = Depends(require_admin)):
    with shared_db_session() as db:
        rows = db.execute(text("SELECT * FROM v_partition_stats")).fetchall()
    return {"partitions": [dict(r._mapping) for r in rows],
            "checked_at": datetime.utcnow().isoformat()}
