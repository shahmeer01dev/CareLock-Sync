"""
API routes for database and system status
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.database import get_hospital_db, get_shared_db
from common.schemas import DatabaseStatus, SystemStatus
from common.models import Patient, Encounter, LabResult, Medication

router = APIRouter(
    prefix="/api/v1/status",
    tags=["status"]
)


@router.get("/database/hospital", response_model=DatabaseStatus)
async def hospital_database_status(db: Session = Depends(get_hospital_db)):
    """
    Get hospital database status and statistics
    """
    try:
        # Test connection
        db.execute(text("SELECT 1"))
        
        # Get counts
        total_patients = db.query(Patient).count()
        total_encounters = db.query(Encounter).count()
        total_lab_results = db.query(LabResult).count()
        total_medications = db.query(Medication).count()
        
        return {
            "database_name": "hospital_db",
            "connected": True,
            "total_patients": total_patients,
            "total_encounters": total_encounters,
            "total_lab_results": total_lab_results,
            "total_medications": total_medications,
            "last_checked": datetime.utcnow()
        }
    except Exception as e:
        return {
            "database_name": "hospital_db",
            "connected": False,
            "last_checked": datetime.utcnow()
        }


@router.get("/database/shared", response_model=DatabaseStatus)
async def shared_database_status(db: Session = Depends(get_shared_db)):
    """
    Get shared database status and statistics
    """
    try:
        # Test connection
        db.execute(text("SELECT 1"))
        
        # Get counts from FHIR tables
        result = db.execute(text("SELECT COUNT(*) FROM fhir_patient")).scalar()
        total_patients = result or 0
        
        result = db.execute(text("SELECT COUNT(*) FROM fhir_encounter")).scalar()
        total_encounters = result or 0
        
        result = db.execute(text("SELECT COUNT(*) FROM fhir_observation")).scalar()
        total_lab_results = result or 0
        
        result = db.execute(text("SELECT COUNT(*) FROM fhir_medication_request")).scalar()
        total_medications = result or 0
        
        return {
            "database_name": "carelock_shared",
            "connected": True,
            "total_patients": total_patients,
            "total_encounters": total_encounters,
            "total_lab_results": total_lab_results,
            "total_medications": total_medications,
            "last_checked": datetime.utcnow()
        }
    except Exception as e:
        return {
            "database_name": "carelock_shared",
            "connected": False,
            "last_checked": datetime.utcnow()
        }


@router.get("/system", response_model=SystemStatus)
async def system_status(
    hospital_db: Session = Depends(get_hospital_db),
    shared_db: Session = Depends(get_shared_db)
):
    """
    Get overall system status including all databases
    """
    # Get hospital DB status
    try:
        hospital_db.execute(text("SELECT 1"))
        total_patients = hospital_db.query(Patient).count()
        total_encounters = hospital_db.query(Encounter).count()
        total_lab_results = hospital_db.query(LabResult).count()
        total_medications = hospital_db.query(Medication).count()
        
        hospital_status = {
            "database_name": "hospital_db",
            "connected": True,
            "total_patients": total_patients,
            "total_encounters": total_encounters,
            "total_lab_results": total_lab_results,
            "total_medications": total_medications,
            "last_checked": datetime.utcnow()
        }
    except Exception:
        hospital_status = {
            "database_name": "hospital_db",
            "connected": False,
            "last_checked": datetime.utcnow()
        }
    
    # Get shared DB status
    try:
        shared_db.execute(text("SELECT 1"))
        
        result = shared_db.execute(text("SELECT COUNT(*) FROM fhir_patient")).scalar()
        total_patients = result or 0
        
        result = shared_db.execute(text("SELECT COUNT(*) FROM fhir_encounter")).scalar()
        total_encounters = result or 0
        
        result = shared_db.execute(text("SELECT COUNT(*) FROM fhir_observation")).scalar()
        total_lab_results = result or 0
        
        result = shared_db.execute(text("SELECT COUNT(*) FROM fhir_medication_request")).scalar()
        total_medications = result or 0
        
        shared_status = {
            "database_name": "carelock_shared",
            "connected": True,
            "total_patients": total_patients,
            "total_encounters": total_encounters,
            "total_lab_results": total_lab_results,
            "total_medications": total_medications,
            "last_checked": datetime.utcnow()
        }
    except Exception:
        shared_status = {
            "database_name": "carelock_shared",
            "connected": False,
            "last_checked": datetime.utcnow()
        }
    
    return {
        "api_status": "running",
        "hospital_db": hospital_status,
        "shared_db": shared_status,
        "timestamp": datetime.utcnow()
    }
