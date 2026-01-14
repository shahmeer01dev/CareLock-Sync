def map_patient(row):
    patient_id, name, gender, dob = row

    return {
        "resourceType": "Patient",
        "id": str(patient_id),
        "name": [
            {
                "text": name
            }
        ],
        "gender": gender.lower(),
        "birthDate": str(dob)
    }

def map_encounter(row):
    visit_id, patient_id, visit_date, doctor, diagnosis = row

    return {
        "resourceType": "Encounter",
        "id": str(visit_id),
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "period": {
            "start": str(visit_date)
        },
        "reasonCode": [
            {
                "text": diagnosis
            }
        ],
        "serviceProvider": {
            "display": doctor
        }
    }



def map_observation(row):
    lab_id, patient_id, test_name, result, test_date = row

    return {
        "resourceType": "Observation",
        "id": str(lab_id),
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "code": {
            "text": test_name
        },
        "valueString": result,
        "effectiveDateTime": str(test_date)
    }
