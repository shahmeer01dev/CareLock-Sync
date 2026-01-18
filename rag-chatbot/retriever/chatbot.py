from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from transformers import pipeline

VECTOR_DB_DIR = "../vector_db"

def load_vector_store():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vectordb = Chroma(
        persist_directory=VECTOR_DB_DIR,
        embedding_function=embeddings
    )

    return vectordb

def load_llm():
    """
    Lightweight local text-generation model
    """
    return pipeline(
        "text-generation",
        model="google/flan-t5-base",
        max_length=256
    )

def ask_question(vectordb, llm, question):
    docs = vectordb.similarity_search(question, k=2)

    context = "\n".join([doc.page_content for doc in docs])

    prompt = f"""
You are a clinical assistant.
Answer ONLY using the context below.
If the answer is not in the context, say "Not available in hospital data".

Context:
{context}

Question:
{question}

Answer:
"""

    response = llm(prompt)[0]["generated_text"]
    return response

if __name__ == "__main__":
    print("🔍 Loading vector store...")
    vectordb = load_vector_store()

    print("🤖 Loading local language model...")
    llm = load_llm()

    print("\n✅ CareLock RAG Chatbot Ready\n")

    while True:
        question = input("Ask a clinical question (or type 'exit'): ")
        if question.lower() == "exit":
            break

        answer = ask_question(vectordb, llm, question)
        print("\n🧠 Answer:\n", answer)
        print("-" * 50)
