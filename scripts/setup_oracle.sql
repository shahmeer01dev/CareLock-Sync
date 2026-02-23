-- Create hospital user and tables in Oracle
-- Run with: docker exec -i carelock_oracle sqlplus system/OraclePass123@XE < setup_oracle.sql

-- Create user
CREATE USER hospital_user IDENTIFIED BY hospital_pass;
GRANT CONNECT, RESOURCE, DBA TO hospital_user;
GRANT UNLIMITED TABLESPACE TO hospital_user;

-- Connect as hospital_user
CONNECT hospital_user/hospital_pass@XE;

-- Create tables
CREATE TABLE patients (
    patient_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    medical_record_number VARCHAR2(50) UNIQUE NOT NULL,
    first_name VARCHAR2(100) NOT NULL,
    last_name VARCHAR2(100) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender VARCHAR2(20),
    email VARCHAR2(100)
);

CREATE TABLE encounters (
    encounter_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    patient_id NUMBER NOT NULL,
    encounter_type VARCHAR2(50) NOT NULL,
    admission_date TIMESTAMP NOT NULL,
    status VARCHAR2(50),
    CONSTRAINT fk_enc_patient FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE lab_results (
    lab_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    encounter_id NUMBER NOT NULL,
    test_name VARCHAR2(200) NOT NULL,
    result_value VARCHAR2(200),
    CONSTRAINT fk_lab_encounter FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
);

CREATE TABLE medications (
    medication_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    encounter_id NUMBER NOT NULL,
    medication_name VARCHAR2(200) NOT NULL,
    dosage VARCHAR2(100),
    CONSTRAINT fk_med_encounter FOREIGN KEY (encounter_id) REFERENCES encounters(encounter_id)
);

CREATE TABLE data_change_log (
    change_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    table_name VARCHAR2(100) NOT NULL,
    operation VARCHAR2(10) NOT NULL,
    record_id NUMBER,
    old_data CLOB,
    new_data CLOB,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample data
INSERT INTO patients (medical_record_number, first_name, last_name, date_of_birth, gender, email)
VALUES ('MRN-ORACLE-00001', 'John', 'Oracle', TO_DATE('1980-01-15', 'YYYY-MM-DD'), 'male', 'john.oracle@test.com');

INSERT INTO patients (medical_record_number, first_name, last_name, date_of_birth, gender, email)
VALUES ('MRN-ORACLE-00002', 'Jane', 'Database', TO_DATE('1985-05-20', 'YYYY-MM-DD'), 'female', 'jane.db@test.com');

INSERT INTO encounters (patient_id, encounter_type, admission_date, status)
VALUES (1, 'Emergency', SYSTIMESTAMP, 'finished');

INSERT INTO encounters (patient_id, encounter_type, admission_date, status)
VALUES (2, 'Outpatient', SYSTIMESTAMP, 'finished');

INSERT INTO lab_results (encounter_id, test_name, result_value)
VALUES (1, 'CBC', '12.5');

INSERT INTO medications (encounter_id, medication_name, dosage)
VALUES (1, 'Aspirin', '100mg');

COMMIT;

-- Verify
SELECT 'Patients: ' || COUNT(*) FROM patients;
SELECT 'Encounters: ' || COUNT(*) FROM encounters;
SELECT 'Lab Results: ' || COUNT(*) FROM lab_results;
SELECT 'Medications: ' || COUNT(*) FROM medications;

EXIT;
