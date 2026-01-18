-- Fake Hospital Database for CareLock Sync
-- This simulates an on-premises hospital system

CREATE TABLE patients (
    patient_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100),
    gender VARCHAR(10),
    date_of_birth DATE
);

CREATE TABLE visits (
    visit_id SERIAL PRIMARY KEY,
    patient_id INT,
    visit_date DATE,
    doctor_name VARCHAR(100),
    diagnosis TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

CREATE TABLE labs (
    lab_id SERIAL PRIMARY KEY,
    patient_id INT,
    test_name VARCHAR(100),
    test_result VARCHAR(50),
    test_date DATE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
);

-- Insert Fake Patients
INSERT INTO patients (full_name, gender, date_of_birth) VALUES
('Ali Khan', 'Male', '1995-04-12'),
('Sara Ahmed', 'Female', '1990-08-23'),
('Usman Raza', 'Male', '1985-01-17');

-- Insert Fake Visits
INSERT INTO visits (patient_id, visit_date, doctor_name, diagnosis) VALUES
(1, '2024-11-01', 'Dr. Ayesha', 'Flu'),
(2, '2024-11-03', 'Dr. Hamza', 'Diabetes'),
(3, '2024-11-05', 'Dr. Sana', 'Hypertension');

-- Insert Fake Lab Results
INSERT INTO labs (patient_id, test_name, test_result, test_date) VALUES
(1, 'CBC', 'Normal', '2024-11-01'),
(2, 'Blood Sugar', 'High', '2024-11-03'),
(3, 'Blood Pressure', 'High', '2024-11-05');
