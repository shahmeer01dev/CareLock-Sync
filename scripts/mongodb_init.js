// MongoDB Database Initialization Script
// Creates collections and populates with fake data

db = db.getSiblingDB('hospital_db_mongodb');

// Create collections
db.createCollection('patients');
db.createCollection('encounters');
db.createCollection('lab_results');
db.createCollection('medications');
db.createCollection('change_log');

// Create indexes
db.patients.createIndex({ medical_record_number: 1 }, { unique: true });
db.patients.createIndex({ last_name: 1 });
db.encounters.createIndex({ patient_id: 1 });
db.lab_results.createIndex({ encounter_id: 1 });
db.medications.createIndex({ encounter_id: 1 });
db.change_log.createIndex({ table_name: 1 });
db.change_log.createIndex({ changed_at: 1 });

// Insert sample patients
db.patients.insertMany([
    {
        medical_record_number: 'MRN-MONGO-00001',
        first_name: 'Alice',
        last_name: 'Cooper',
        date_of_birth: new Date('1985-04-12'),
        gender: 'female',
        blood_type: 'A+',
        phone_number: '555-0201',
        email: 'alice.cooper@email.com',
        address: {
            line1: '100 Broadway',
            city: 'New York',
            state: 'NY',
            zip_code: '10001'
        },
        created_at: new Date(),
        updated_at: new Date()
    },
    {
        medical_record_number: 'MRN-MONGO-00002',
        first_name: 'Bob',
        last_name: 'Dylan',
        date_of_birth: new Date('1990-06-20'),
        gender: 'male',
        blood_type: 'O+',
        phone_number: '555-0202',
        email: 'bob.dylan@email.com',
        address: {
            line1: '200 Fifth Ave',
            city: 'Brooklyn',
            state: 'NY',
            zip_code: '11201'
        },
        created_at: new Date(),
        updated_at: new Date()
    },
    {
        medical_record_number: 'MRN-MONGO-00003',
        first_name: 'Carol',
        last_name: 'King',
        date_of_birth: new Date('1978-09-15'),
        gender: 'female',
        blood_type: 'B+',
        phone_number: '555-0203',
        email: 'carol.king@email.com',
        address: {
            line1: '300 Madison Ave',
            city: 'Queens',
            state: 'NY',
            zip_code: '11101'
        },
        created_at: new Date(),
        updated_at: new Date()
    }
]);

// Get patient IDs
const patient1 = db.patients.findOne({ medical_record_number: 'MRN-MONGO-00001' })._id;
const patient2 = db.patients.findOne({ medical_record_number: 'MRN-MONGO-00002' })._id;
const patient3 = db.patients.findOne({ medical_record_number: 'MRN-MONGO-00003' })._id;

// Insert encounters
db.encounters.insertMany([
    {
        patient_id: patient1,
        encounter_type: 'Outpatient',
        admission_date: new Date('2024-01-10T09:00:00'),
        discharge_date: new Date('2024-01-10T10:30:00'),
        chief_complaint: 'Flu symptoms',
        diagnosis: 'Influenza',
        attending_physician: 'Dr. House',
        status: 'finished',
        created_at: new Date()
    },
    {
        patient_id: patient2,
        encounter_type: 'Emergency',
        admission_date: new Date('2024-01-25T22:00:00'),
        discharge_date: new Date('2024-01-26T03:00:00'),
        chief_complaint: 'Broken arm',
        diagnosis: 'Fracture radius',
        attending_physician: 'Dr. Grey',
        status: 'finished',
        created_at: new Date()
    },
    {
        patient_id: patient3,
        encounter_type: 'Inpatient',
        admission_date: new Date('2024-02-05T14:00:00'),
        discharge_date: new Date('2024-02-08T10:00:00'),
        chief_complaint: 'Pneumonia',
        diagnosis: 'Bacterial pneumonia',
        attending_physician: 'Dr. Wilson',
        status: 'finished',
        created_at: new Date()
    }
]);

// Get encounter IDs
const encounter1 = db.encounters.findOne({ patient_id: patient1 })._id;
const encounter2 = db.encounters.findOne({ patient_id: patient2 })._id;
const encounter3 = db.encounters.findOne({ patient_id: patient3 })._id;

// Insert lab results
db.lab_results.insertMany([
    {
        encounter_id: encounter1,
        patient_id: patient1,
        test_name: 'Rapid Flu Test',
        test_code: 'FLU',
        result_value: 'Positive',
        result_unit: '',
        performed_date: new Date('2024-01-10T09:30:00'),
        created_at: new Date()
    },
    {
        encounter_id: encounter2,
        patient_id: patient2,
        test_name: 'X-Ray Arm',
        test_code: 'XRAY-ARM',
        result_value: 'Fracture identified',
        result_unit: '',
        performed_date: new Date('2024-01-25T22:30:00'),
        created_at: new Date()
    },
    {
        encounter_id: encounter3,
        patient_id: patient3,
        test_name: 'Chest X-Ray',
        test_code: 'XRAY-CHEST',
        result_value: 'Infiltrate present',
        result_unit: '',
        performed_date: new Date('2024-02-05T15:00:00'),
        created_at: new Date()
    }
]);

// Insert medications
db.medications.insertMany([
    {
        encounter_id: encounter1,
        patient_id: patient1,
        medication_name: 'Oseltamivir 75mg',
        dosage: '1 capsule',
        frequency: 'twice daily',
        route: 'oral',
        start_date: new Date('2024-01-10'),
        status: 'completed',
        created_at: new Date()
    },
    {
        encounter_id: encounter2,
        patient_id: patient2,
        medication_name: 'Ibuprofen 800mg',
        dosage: '1 tablet',
        frequency: 'three times daily',
        route: 'oral',
        start_date: new Date('2024-01-25'),
        status: 'active',
        created_at: new Date()
    },
    {
        encounter_id: encounter3,
        patient_id: patient3,
        medication_name: 'Amoxicillin 500mg',
        dosage: '1 capsule',
        frequency: 'three times daily',
        route: 'oral',
        start_date: new Date('2024-02-05'),
        status: 'active',
        created_at: new Date()
    }
]);

print('MongoDB initialization complete!');
print('Patients: ' + db.patients.count());
print('Encounters: ' + db.encounters.count());
print('Lab Results: ' + db.lab_results.count());
print('Medications: ' + db.medications.count());
