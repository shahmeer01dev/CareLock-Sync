-- MySQL Database Initialization Script
-- Creates tables and populates with fake data

CREATE DATABASE IF NOT EXISTS hospital_db_mysql;
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
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
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
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
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
    performed_date DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
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
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id),
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
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
    INDEX idx_table (table_name),
    INDEX idx_time (changed_at)
) ENGINE=InnoDB;

-- Insert sample data
INSERT INTO patients (medical_record_number, first_name, last_name, date_of_birth, gender, blood_type, phone_number, email, address_line1, city, state, zip_code) VALUES
('MRN-MYSQL-00001', 'John', 'Smith', '1980-05-15', 'male', 'A+', '555-0101', 'john.smith@email.com', '123 Main St', 'Springfield', 'IL', '62701'),
('MRN-MYSQL-00002', 'Jane', 'Doe', '1992-08-22', 'female', 'B+', '555-0102', 'jane.doe@email.com', '456 Oak Ave', 'Chicago', 'IL', '60601'),
('MRN-MYSQL-00003', 'Robert', 'Johnson', '1975-03-10', 'male', 'O+', '555-0103', 'robert.j@email.com', '789 Pine Rd', 'Peoria', 'IL', '61602'),
('MRN-MYSQL-00004', 'Mary', 'Williams', '1988-11-30', 'female', 'AB+', '555-0104', 'mary.w@email.com', '321 Elm St', 'Rockford', 'IL', '61101'),
('MRN-MYSQL-00005', 'Michael', 'Brown', '1995-07-18', 'male', 'A-', '555-0105', 'michael.b@email.com', '654 Maple Dr', 'Naperville', 'IL', '60540');

INSERT INTO encounters (patient_id, encounter_type, admission_date, discharge_date, chief_complaint, diagnosis, attending_physician, status) VALUES
(1, 'Emergency', '2024-01-15 10:30:00', '2024-01-15 18:45:00', 'Chest pain', 'Angina pectoris', 'Dr. Anderson', 'finished'),
(2, 'Outpatient', '2024-01-20 09:00:00', '2024-01-20 10:30:00', 'Annual checkup', 'Routine examination', 'Dr. Martinez', 'finished'),
(3, 'Inpatient', '2024-02-01 14:20:00', '2024-02-05 11:00:00', 'Severe headache', 'Migraine', 'Dr. Chen', 'finished'),
(4, 'Emergency', '2024-02-10 22:15:00', '2024-02-11 02:30:00', 'Abdominal pain', 'Appendicitis', 'Dr. Patel', 'finished'),
(5, 'Outpatient', '2024-02-15 11:00:00', '2024-02-15 12:00:00', 'Follow-up', 'Diabetes management', 'Dr. Thompson', 'finished');

INSERT INTO lab_results (encounter_id, patient_id, test_name, test_code, result_value, result_unit, performed_date) VALUES
(1, 1, 'Troponin', 'TROP', '0.02', 'ng/mL', '2024-01-15 11:00:00'),
(2, 2, 'Complete Blood Count', 'CBC', '12.5', 'g/dL', '2024-01-20 09:30:00'),
(3, 3, 'CT Scan Brain', 'CT-BRAIN', 'Normal', '', '2024-02-01 15:00:00'),
(4, 4, 'WBC Count', 'WBC', '15000', 'cells/uL', '2024-02-10 23:00:00'),
(5, 5, 'Glucose Fasting', 'GLU-F', '126', 'mg/dL', '2024-02-15 11:15:00');

INSERT INTO medications (encounter_id, patient_id, medication_name, dosage, frequency, route, start_date, status) VALUES
(1, 1, 'Aspirin 81mg', '1 tablet', 'once daily', 'oral', '2024-01-15', 'active'),
(2, 2, 'Multivitamin', '1 tablet', 'once daily', 'oral', '2024-01-20', 'active'),
(3, 3, 'Sumatriptan 50mg', '1 tablet', 'as needed', 'oral', '2024-02-01', 'active'),
(4, 4, 'Ciprofloxacin 500mg', '1 tablet', 'twice daily', 'oral', '2024-02-10', 'completed'),
(5, 5, 'Metformin 1000mg', '1 tablet', 'twice daily', 'oral', '2024-02-15', 'active');
