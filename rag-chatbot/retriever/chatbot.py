from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from transformers import pipeline

VECTOR_DB_DIR = "../vector_db"

def load_vector_store():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    return Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)

def load_llm():
    # T5 is a text-to-text model, so we use that pipeline type
    return pipeline(
        "text2text-generation",
        model="google/flan-t5-base",
        max_length=512
    )

def ask_question(vectordb, llm, question):
    # 1. Retrieve relevant data
    docs = vectordb.similarity_search(question, k=3)
    context = "\n---\n".join([doc.page_content for doc in docs])

    # 2. Formulate the prompt
    prompt = f"""Use the following context to answer the question. 
If the answer is not in the context, say "Data not available".

Context:
{context}

Question: {question}
Answer:"""

    # 3. Generate Answer
    # T5 returns a list of dicts: [{'generated_text': 'The Answer'}]
    result = llm(prompt)
    return result[0]['generated_text']

if __name__ == "__main__":
    print("🔍 Loading vector store...")
    vectordb = load_vector_store()

    print("🤖 Loading AI Model (Flan-T5)...")
    llm = load_llm()

    print("\n✅ CareLock RAG Chatbot Ready\n")

    while True:
        question = input("Ask a clinical question (or type 'exit'): ")
        if question.lower() == "exit":
            break

        print("\n🤔 Thinking...")
        answer = ask_question(vectordb, llm, question)
        print(f"🧠 Answer: {answer}")
        print("-" * 50)