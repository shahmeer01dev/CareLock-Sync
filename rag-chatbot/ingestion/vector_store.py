from db_reader import fetch_fhir_patients, fhir_patient_to_text
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
import os

# Directory where vectors will be stored
VECTOR_DB_DIR = "../vector_db"

def build_vector_store():
    print("Loading FHIR patient data from central DB...")
    rows = fetch_fhir_patients()

    documents = []
    for row in rows:
        patient_resource = row[0]
        text = fhir_patient_to_text(patient_resource)
        documents.append(text)

    print(f"Total documents prepared: {len(documents)}")

    # Local embedding model (safe for FYP, no API key)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # Create / persist ChromaDB
    vectordb = Chroma.from_texts(
        documents,
        embedding=embeddings,
        persist_directory=VECTOR_DB_DIR
    )

    vectordb.persist()
    print("✅ Vector store created successfully!")

if __name__ == "__main__":
    build_vector_store()
