CREATE TABLE fhir_patient (
    id TEXT PRIMARY KEY,
    tenant_id TEXT,
    resource JSONB
);

CREATE TABLE fhir_encounter (
    id TEXT PRIMARY KEY,
    tenant_id TEXT,
    resource JSONB
);

CREATE TABLE fhir_observation (
    id TEXT PRIMARY KEY,
    tenant_id TEXT,
    resource JSONB
);
