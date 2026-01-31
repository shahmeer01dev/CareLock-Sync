"""
SQLAlchemy ORM models for Hospital Database
"""
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Patient(Base):
    """Patient model - represents patient demographic information"""
    __tablename__ = 'patients'
    
    patient_id = Column(Integer, primary_key=True, index=True)
    medical_record_number = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False, index=True)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20))
    blood_type = Column(String(10))
    phone_number = Column(String(20))
    email = Column(String(100))
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    emergency_contact_name = Column(String(200))
    emergency_contact_phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    encounters = relationship("Encounter", back_populates="patient")
    lab_results = relationship("LabResult", back_populates="patient")
    medications = relationship("Medication", back_populates="patient")
    
    def __repr__(self):
        return f"<Patient(id={self.patient_id}, mrn={self.medical_record_number}, name={self.first_name} {self.last_name})>"


class Encounter(Base):
    """Encounter model - represents hospital visits"""
    __tablename__ = 'encounters'
    
    encounter_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False, index=True)
    encounter_type = Column(String(50), nullable=False)
    admission_date = Column(DateTime, nullable=False, index=True)
    discharge_date = Column(DateTime)
    chief_complaint = Column(Text)
    diagnosis = Column(Text)
    attending_physician = Column(String(200))
    department = Column(String(100))
    room_number = Column(String(20))
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="encounters")
    lab_results = relationship("LabResult", back_populates="encounter")
    medications = relationship("Medication", back_populates="encounter")
    
    def __repr__(self):
        return f"<Encounter(id={self.encounter_id}, patient_id={self.patient_id}, type={self.encounter_type})>"


class LabResult(Base):
    """LabResult model - represents laboratory test results"""
    __tablename__ = 'lab_results'
    
    lab_id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey('encounters.encounter_id'), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False, index=True)
    test_name = Column(String(200), nullable=False)
    test_code = Column(String(50))
    result_value = Column(String(200))
    result_unit = Column(String(50))
    reference_range = Column(String(100))
    abnormal_flag = Column(String(20))
    performed_date = Column(DateTime, nullable=False)
    result_date = Column(DateTime)
    performing_lab = Column(String(200))
    technician_name = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="lab_results")
    encounter = relationship("Encounter", back_populates="lab_results")
    
    def __repr__(self):
        return f"<LabResult(id={self.lab_id}, test={self.test_name}, value={self.result_value})>"


class Medication(Base):
    """Medication model - represents prescribed medications"""
    __tablename__ = 'medications'
    
    medication_id = Column(Integer, primary_key=True, index=True)
    encounter_id = Column(Integer, ForeignKey('encounters.encounter_id'), nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey('patients.patient_id'), nullable=False, index=True)
    medication_name = Column(String(200), nullable=False)
    dosage = Column(String(100))
    frequency = Column(String(100))
    route = Column(String(50))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    prescribing_physician = Column(String(200))
    pharmacy_notes = Column(Text)
    status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = relationship("Patient", back_populates="medications")
    encounter = relationship("Encounter", back_populates="medications")
    
    def __repr__(self):
        return f"<Medication(id={self.medication_id}, name={self.medication_name}, status={self.status})>"
