"""
generate_fhir_mappings.py
Generates the complete expanded fhir_mappings.json with real-world aliases.
Run once to produce the training data for the vector store.
"""
import json, os

PATIENT_MAPPINGS = [
    # IDs
    ("patient_id","id","integer","to_string"),("pt_id","id","integer","to_string"),
    # MRN variants
    ("medical_record_number","identifier[0].value","string",None),
    ("mrn","identifier[0].value","string",None),
    ("chart_number","identifier[0].value","string",None),
    ("patient_number","identifier[0].value","string",None),
    ("accession_number","identifier[0].value","string",None),
    # First name variants
    ("first_name","name[0].given[0]","string",None),
    ("fname","name[0].given[0]","string",None),
    ("pt_fname","name[0].given[0]","string",None),
    ("given_name","name[0].given[0]","string",None),
    ("forename","name[0].given[0]","string",None),
    # Last name variants
    ("last_name","name[0].family","string",None),
    ("lname","name[0].family","string",None),
    ("pt_lname","name[0].family","string",None),
    ("family_name","name[0].family","string",None),
    ("surname","name[0].family","string",None),
    # Date of birth variants
    ("date_of_birth","birthDate","date","format_date"),
    ("dob","birthDate","date","format_date"),
    ("birth_date","birthDate","date","format_date"),
    ("pt_dob","birthDate","date","format_date"),
    ("birthday","birthDate","date","format_date"),
    ("birthdate","birthDate","date","format_date"),
    # Gender variants
    ("gender","gender","code","normalize_gender"),
    ("sex","gender","code","normalize_gender"),
    ("patient_sex","gender","code","normalize_gender"),
    ("pt_sex","gender","code","normalize_gender"),
    ("sex_code","gender","code","normalize_gender"),
    # Phone variants
    ("phone_number","telecom[0].value","string",None),
    ("phone","telecom[0].value","string",None),
    ("mobile","telecom[0].value","string",None),
    ("cell_phone","telecom[0].value","string",None),
    ("contact_number","telecom[0].value","string",None),
    ("telephone","telecom[0].value","string",None),
    # Email variants
    ("email","telecom[1].value","string",None),
    ("email_address","telecom[1].value","string",None),
    ("pt_email","telecom[1].value","string",None),
    # Address variants
    ("address_line1","address[0].line[0]","string",None),
    ("address","address[0].line[0]","string",None),
    ("street_address","address[0].line[0]","string",None),
    ("street","address[0].line[0]","string",None),
    ("city","address[0].city","string",None),
    ("town","address[0].city","string",None),
    ("patient_city","address[0].city","string",None),
    ("state","address[0].state","string",None),
    ("province","address[0].state","string",None),
    ("zip_code","address[0].postalCode","string",None),
    ("zip","address[0].postalCode","string",None),
    ("postal_code","address[0].postalCode","string",None),
    ("postcode","address[0].postalCode","string",None),
    # Extra identifiers
    ("blood_type","extension[0].valueCode","string",None),
    ("blood_group","extension[0].valueCode","string",None),
    ("national_id","identifier[1].value","string",None),
    ("cnic","identifier[1].value","string",None),
    ("insurance_id","identifier[2].value","string",None),
    ("insurance_number","identifier[2].value","string",None),
    # Status/meta
    ("is_active","active","boolean",None),
    ("active","active","boolean",None),
    ("marital_status","maritalStatus.text","string",None),
    ("emergency_contact","contact[0].name.text","string",None),
    ("next_of_kin","contact[0].name.text","string",None),
    ("registration_date","meta.lastUpdated","dateTime","format_datetime"),
    ("created_at","meta.lastUpdated","dateTime","format_datetime"),
    ("nationality","extension[1].valueString","string",None),
]

ENCOUNTER_MAPPINGS = [
    # IDs
    ("encounter_id","id","integer","to_string"),
    ("visit_id","id","integer","to_string"),
    ("admission_id","id","integer","to_string"),
    # Patient ref
    ("patient_id","subject.reference","integer","patient_reference"),
    ("pt_id","subject.reference","integer","patient_reference"),
    # Encounter type/class
    ("encounter_type","class.code","code","map_encounter_class"),
    ("visit_type","class.code","code","map_encounter_class"),
    ("admission_type","class.code","code","map_encounter_class"),
    ("class_code","class.code","code","map_encounter_class"),
    # Dates
    ("admission_date","period.start","dateTime","format_datetime"),
    ("visit_date","period.start","dateTime","format_datetime"),
    ("admit_date","period.start","dateTime","format_datetime"),
    ("admission_dt","period.start","dateTime","format_datetime"),
    ("start_date","period.start","dateTime","format_datetime"),
    ("discharge_date","period.end","dateTime","format_datetime"),
    ("discharge_dt","period.end","dateTime","format_datetime"),
    ("end_date","period.end","dateTime","format_datetime"),
    # Status
    ("status","status","code","map_encounter_status"),
    ("visit_status","status","code","map_encounter_status"),
    ("encounter_status","status","code","map_encounter_status"),
    # Reason/complaint
    ("chief_complaint","reasonCode[0].text","string",None),
    ("complaint","reasonCode[0].text","string",None),
    ("presenting_complaint","reasonCode[0].text","string",None),
    ("reason_for_visit","reasonCode[0].text","string",None),
    # Diagnosis
    ("diagnosis","diagnosis[0].condition.display","string",None),
    ("primary_diagnosis","diagnosis[0].condition.display","string",None),
    ("icd_code","diagnosis[0].condition.coding[0].code","string",None),
    ("diagnosis_code","diagnosis[0].condition.coding[0].code","string",None),
    # Provider
    ("attending_physician","participant[0].individual.display","string",None),
    ("doctor","participant[0].individual.display","string",None),
    ("physician","participant[0].individual.display","string",None),
    ("provider","participant[0].individual.display","string",None),
    # Department
    ("department","serviceType.text","string",None),
    ("ward","serviceType.text","string",None),
    ("clinic","serviceType.text","string",None),
    ("specialty","serviceType.text","string",None),
    # LOS
    ("length_of_stay","length.value","integer",None),
    ("los","length.value","integer",None),
]

OBSERVATION_MAPPINGS = [
    # IDs
    ("lab_id","id","integer","to_string"),
    ("observation_id","id","integer","to_string"),
    ("result_id","id","integer","to_string"),
    # References
    ("patient_id","subject.reference","integer","patient_reference"),
    ("encounter_id","encounter.reference","integer","encounter_reference"),
    ("visit_id","encounter.reference","integer","encounter_reference"),
    # Test code/name
    ("test_name","code.text","string",None),
    ("lab_test","code.text","string",None),
    ("test_description","code.text","string",None),
    ("observation_name","code.text","string",None),
    ("test_code","code.coding[0].code","string",None),
    ("loinc_code","code.coding[0].code","string",None),
    ("lab_code","code.coding[0].code","string",None),
    # Values
    ("result_value","valueQuantity.value","decimal","to_decimal"),
    ("value","valueQuantity.value","decimal","to_decimal"),
    ("numeric_result","valueQuantity.value","decimal","to_decimal"),
    ("lab_value","valueQuantity.value","decimal","to_decimal"),
    # Units
    ("result_unit","valueQuantity.unit","string",None),
    ("unit","valueQuantity.unit","string",None),
    ("units","valueQuantity.unit","string",None),
    ("uom","valueQuantity.unit","string",None),
    # Reference range
    ("reference_range","referenceRange[0].text","string",None),
    ("normal_range","referenceRange[0].text","string",None),
    ("ref_range","referenceRange[0].text","string",None),
    # Flags
    ("abnormal_flag","interpretation[0].coding[0].code","code","map_abnormal_flag"),
    ("flag","interpretation[0].coding[0].code","code","map_abnormal_flag"),
    ("result_flag","interpretation[0].coding[0].code","code","map_abnormal_flag"),
    # Status
    ("status","status","code",None),
    ("result_status","status","code",None),
    # Dates
    ("performed_date","effectiveDateTime","dateTime","format_datetime"),
    ("test_date","effectiveDateTime","dateTime","format_datetime"),
    ("collection_date","effectiveDateTime","dateTime","format_datetime"),
    ("result_date","effectiveDateTime","dateTime","format_datetime"),
    # Category
    ("lab_category","category[0].text","string",None),
    ("panel_name","category[0].text","string",None),
    ("specimen_type","specimen.display","string",None),
    ("sample_type","specimen.display","string",None),
]

MEDICATION_MAPPINGS = [
    # IDs
    ("medication_id","id","integer","to_string"),
    ("prescription_id","id","integer","to_string"),
    ("order_id","id","integer","to_string"),
    # References
    ("patient_id","subject.reference","integer","patient_reference"),
    ("encounter_id","encounter.reference","integer","encounter_reference"),
    # Drug name
    ("medication_name","medicationCodeableConcept.text","string",None),
    ("drug_name","medicationCodeableConcept.text","string",None),
    ("medicine","medicationCodeableConcept.text","string",None),
    ("drug","medicationCodeableConcept.text","string",None),
    ("medication_code","medicationCodeableConcept.coding[0].code","string",None),
    ("ndc_code","medicationCodeableConcept.coding[0].code","string",None),
    # Identifier
    ("rx_number","identifier[0].value","string",None),
    ("prescription_number","identifier[0].value","string",None),
    # Dosage
    ("dosage","dosageInstruction[0].doseAndRate[0].doseQuantity.value","string","extract_dosage_value"),
    ("dose","dosageInstruction[0].doseAndRate[0].doseQuantity.value","string","extract_dosage_value"),
    ("dose_amount","dosageInstruction[0].doseAndRate[0].doseQuantity.value","string","extract_dosage_value"),
    ("strength","dosageInstruction[0].doseAndRate[0].doseQuantity.value","string","extract_dosage_value"),
    # Frequency/sig
    ("frequency","dosageInstruction[0].timing.code.text","string",None),
    ("sig","dosageInstruction[0].timing.code.text","string",None),
    ("instructions","dosageInstruction[0].timing.code.text","string",None),
    # Route
    ("route","dosageInstruction[0].route.text","string",None),
    ("route_of_administration","dosageInstruction[0].route.text","string",None),
    ("administration_route","dosageInstruction[0].route.text","string",None),
    # Dates
    ("start_date","authoredOn","date","format_date"),
    ("prescribed_date","authoredOn","date","format_date"),
    ("order_date","authoredOn","date","format_date"),
    ("prescription_date","authoredOn","date","format_date"),
    # Status
    ("status","status","code","map_medication_status"),
    ("rx_status","status","code","map_medication_status"),
    # Prescriber
    ("prescriber","requester.display","string",None),
    ("prescribing_physician","requester.display","string",None),
    # Dispense
    ("quantity","dispenseRequest.quantity.value","decimal","to_decimal"),
    ("days_supply","dispenseRequest.expectedSupplyDuration.value","integer",None),
    ("refills","dispenseRequest.numberOfRepeatsAllowed","integer",None),
]

def build_field_list(tuples):
    result = []
    for t in tuples:
        src, tgt, dtype, xform = t
        result.append({
            "source_field": src,
            "target_path":  tgt,
            "data_type":    dtype,
            "required":     tgt in ("id","identifier[0].value","name[0].given[0]","name[0].family","birthDate","subject.reference"),
            "transformation": xform
        })
    return result

output = {
    "patient":            {"source_table": "patients",    "target_resource": "Patient",           "field_mappings": build_field_list(PATIENT_MAPPINGS)},
    "encounter":          {"source_table": "encounters",  "target_resource": "Encounter",          "field_mappings": build_field_list(ENCOUNTER_MAPPINGS)},
    "observation":        {"source_table": "lab_results", "target_resource": "Observation",        "field_mappings": build_field_list(OBSERVATION_MAPPINGS)},
    "medication_request": {"source_table": "medications", "target_resource": "MedicationRequest",  "field_mappings": build_field_list(MEDICATION_MAPPINGS)},
}

out_path = os.path.join(os.path.dirname(__file__), "schema_mapper", "fhir_mappings.json")
with open(out_path, "w") as f:
    json.dump(output, f, indent=2)

total = sum(len(v["field_mappings"]) for v in output.values())
print(f"Written {total} mappings to {out_path}")
for k, v in output.items():
    print(f"  {k:22s}: {len(v['field_mappings'])} entries")
