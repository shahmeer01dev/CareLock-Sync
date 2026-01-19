from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chatbot import load_vector_store, load_llm, ask_question

app = FastAPI(title="CareLock AI Chatbot")

# Global variables to hold the model in memory
vectordb = None
llm = None

class QueryRequest(BaseModel):
    question: str

@app.on_event("startup")
def startup_event():
    global vectordb, llm
    print("🤖 Booting up AI Brain (this takes a moment)...")
    vectordb = load_vector_store()
    llm = load_llm()
    print("✅ AI Ready to Serve.")

@app.post("/chat")
def chat_endpoint(request: QueryRequest):
    if not vectordb or not llm:
        raise HTTPException(status_code=503, detail="AI is still loading...")
    
    try:
        answer = ask_question(vectordb, llm, request.question)
        return {"question": request.question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health():
    return {"status": "active", "model_loaded": vectordb is not None}