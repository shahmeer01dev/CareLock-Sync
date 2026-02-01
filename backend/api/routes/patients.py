"""
API routes for patient operations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.database import get_hospital_db
from common.models import Patient
from common.schemas import PatientResponse, PatientList

router = APIRouter(
    prefix="/api/v1/patients",
    tags=["patients"]
)


@router.get("/", response_model=PatientList)
async def get_patients(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_hospital_db)
):
    """
    Get list of patients with pagination
    """
    # Get total count
    total = db.query(Patient).count()
    
    # Get patients with pagination
    patients = db.query(Patient).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "patients": patients
    }


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: Session = Depends(get_hospital_db)
):
    """
    Get a specific patient by ID
    """
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail=f"Patient with ID {patient_id} not found")
    
    return patient


@router.get("/mrn/{medical_record_number}", response_model=PatientResponse)
async def get_patient_by_mrn(
    medical_record_number: str,
    db: Session = Depends(get_hospital_db)
):
    """
    Get a patient by medical record number
    """
    patient = db.query(Patient).filter(
        Patient.medical_record_number == medical_record_number
    ).first()
    
    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient with MRN {medical_record_number} not found"
        )
    
    return patient


@router.get("/search/", response_model=PatientList)
async def search_patients(
    first_name: str = Query(None, description="Search by first name"),
    last_name: str = Query(None, description="Search by last name"),
    blood_type: str = Query(None, description="Filter by blood type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_hospital_db)
):
    """
    Search patients by various criteria
    """
    query = db.query(Patient)
    
    if first_name:
        query = query.filter(Patient.first_name.ilike(f"%{first_name}%"))
    
    if last_name:
        query = query.filter(Patient.last_name.ilike(f"%{last_name}%"))
    
    if blood_type:
        query = query.filter(Patient.blood_type == blood_type)
    
    total = query.count()
    patients = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "patients": patients
    }
