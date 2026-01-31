"""
API routes for connector operations
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import sys
import os

# Fix import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
api_dir = os.path.dirname(current_dir)
backend_dir = os.path.dirname(api_dir)
sys.path.insert(0, backend_dir)

# Now import with correct paths
from common.config import settings
from connector.schema_discovery import SchemaDiscovery
from connector.cdc_monitor import CDCMonitor

router = APIRouter(
    prefix="/api/v1/connector",
    tags=["connector"]
)

# Pydantic models for responses
class SchemaInfo(BaseModel):
    """Schema information response"""
    database: str
    total_tables: int
    tables: Dict[str, Any]
    discovered_at: str


class ChangeRecord(BaseModel):
    """Change record response"""
    change_id: int
    table_name: str
    operation: str
    record_id: Optional[int]
    changed_at: str
    user_name: Optional[str]


class ChangeStats(BaseModel):
    """Change statistics response"""
    statistics: Dict[str, Dict[str, int]]
    total_changes: int


class ConnectorStatus(BaseModel):
    """Connector status response"""
    status: str
    cdc_enabled: bool
    monitored_tables: List[str]
    schema_discovered: bool
    last_sync: Optional[str]


@router.get("/schema", response_model=SchemaInfo)
async def discover_schema():
    """
    Discover and return hospital database schema
    """
    try:
        discovery = SchemaDiscovery(settings.hospital_db_url)
        schema = discovery.get_complete_schema()
        return schema
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema discovery failed: {str(e)}")


@router.get("/schema/table/{table_name}")
async def get_table_schema(table_name: str):
    """
    Get schema for a specific table
    """
    try:
        discovery = SchemaDiscovery(settings.hospital_db_url)
        
        # Check if table exists
        tables = discovery.get_all_tables()
        if table_name not in tables:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        schema = discovery.get_table_schema(table_name)
        return schema
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table schema: {str(e)}")


@router.get("/schema/relationships")
async def get_relationships():
    """
    Get all table relationships
    """
    try:
        discovery = SchemaDiscovery(settings.hospital_db_url)
        relationships = discovery.get_table_relationships()
        return {
            "total_relationships": sum(len(rels) for rels in relationships.values()),
            "relationships": relationships
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get relationships: {str(e)}")


@router.post("/cdc/setup")
async def setup_cdc(table_names: Optional[List[str]] = None):
    """
    Setup Change Data Capture for specified tables
    """
    try:
        monitor = CDCMonitor(settings.hospital_db_url)
        
        # If no tables specified, use default tables
        if not table_names:
            table_names = ['patients', 'encounters', 'lab_results', 'medications']
        
        monitor.setup_cdc_for_tables(table_names)
        
        return {
            "status": "success",
            "message": "CDC setup complete",
            "monitored_tables": table_names,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CDC setup failed: {str(e)}")


@router.get("/cdc/changes", response_model=List[ChangeRecord])
async def get_changes(
    table_name: Optional[str] = Query(None, description="Filter by table name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of changes")
):
    """
    Get recent database changes
    """
    try:
        monitor = CDCMonitor(settings.hospital_db_url)
        changes = monitor.get_recent_changes(table_name=table_name, limit=limit)
        return changes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get changes: {str(e)}")


@router.get("/cdc/statistics", response_model=ChangeStats)
async def get_change_statistics():
    """
    Get statistics about database changes
    """
    try:
        monitor = CDCMonitor(settings.hospital_db_url)
        stats = monitor.get_change_statistics()
        
        # Calculate total changes
        total = sum(sum(ops.values()) for ops in stats.values())
        
        return {
            "statistics": stats,
            "total_changes": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/status", response_model=ConnectorStatus)
async def connector_status():
    """
    Get connector status information
    """
    try:
        # Check if CDC is set up by querying change log table
        monitor = CDCMonitor(settings.hospital_db_url)
        
        try:
            changes = monitor.get_recent_changes(limit=1)
            cdc_enabled = True
            last_change = changes[0]['changed_at'] if changes else None
        except:
            cdc_enabled = False
            last_change = None
        
        # Get monitored tables
        monitored_tables = ['patients', 'encounters', 'lab_results', 'medications']
        
        return {
            "status": "operational",
            "cdc_enabled": cdc_enabled,
            "monitored_tables": monitored_tables,
            "schema_discovered": True,
            "last_sync": last_change
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")
