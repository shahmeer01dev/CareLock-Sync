-- MySQL Hospital Database Setup
-- Drop database if exists
DROP DATABASE IF EXISTS hospital_db_mysql;

-- Create database
CREATE DATABASE hospital_db_mysql
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE hospital_db_mysql;

-- Patients Table
CREATE TABLE patients (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    medical_record_number VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR(20),
    blood_type VARCHAR(10),
    phone_number VARCHAR(20),
    email VARCHAR(100),
    address_line1 VARCHAR(200),
    address_line2 VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    emergency_contact_name VARCHAR(200),
    emergency_contact_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_last_name (last_name),
    INDEX idx_mrn (medical_record_number)
) ENGINE=InnoDB;

-- Encounters Table
CREATE TABLE encounters (
    encounter_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT NOT NULL,
    encounter_type VARCHAR(50) NOT NULL,
    admission_date DATETIME NOT NULL,
    discharge_date DATETIME,
    chief_complaint TEXT,
    diagnosis TEXT,
    attending_physician VARCHAR(200),
    department VARCHAR(100),
    room_number VARCHAR(20),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    INDEX idx_patient (patient_id),
    INDEX idx_admission (admission_date)
) ENGINE=InnoDB;

-- Lab Results Table
CREATE TABLE lab_results (
    lab_id INT AUTO_INCREMENT PRIMARY KEY,
    encounter_id INT NOT NULL,
    patient_id INT NOT NULL,
    test_name VARCHAR(200) NOT NULL,
    test_code VARCHAR(50),
    result_value VARCHAR(200),
    result_unit VARCHAR(50),
    reference_range VARCHAR(100),
    abnormal_flag VARCHAR(20),
    performed_date DATETIME NOT NULL,
    result_date DATETIME,
    performing_lab VARCHAR(200),
    technician_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    INDEX idx_encounter (encounter_id),
    INDEX idx_patient (patient_id)
) ENGINE=InnoDB;

-- Medications Table
CREATE TABLE medications (
    medication_id INT AUTO_INCREMENT PRIMARY KEY,
    encounter_id INT NOT NULL,
    patient_id INT NOT NULL,
    medication_name VARCHAR(200) NOT NULL,
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    route VARCHAR(50),
    start_date DATE NOT NULL,
    end_date DATE,
    prescribing_physician VARCHAR(200),
    pharmacy_notes TEXT,
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    INDEX idx_encounter (encounter_id),
    INDEX idx_patient (patient_id)
) ENGINE=InnoDB;

-- CDC Change Log Table
CREATE TABLE data_change_log (
    change_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    record_id INT,
    old_data JSON,
    new_data JSON,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_name VARCHAR(100),
    change_metadata JSON,
    INDEX idx_table (table_name),
    INDEX idx_time (changed_at)
) ENGINE=InnoDB;
