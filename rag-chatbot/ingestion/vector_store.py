from db_reader import fetch_data_for_rag
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
import shutil

VECTOR_DB_DIR = "../vector_db"

def build_vector_store():
    # Clear old DB to prevent duplicates
    if os.path.exists(VECTOR_DB_DIR):
        shutil.rmtree(VECTOR_DB_DIR)

    print("🔌 Fetching unified clinical data (Patients + Labs)...")
    documents = fetch_data_for_rag()

    print(f"📚 preparing to embed {len(documents)} clinical records...")

    # Local embedding model
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
    print("✅ Vector store created successfully! The brain is updated.")

if __name__ == "__main__":
    build_vector_store()