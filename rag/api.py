from fastapi import FastAPI
from pydantic import BaseModel
from .query import answer_question  # uses your Gemini RAG logic

app = FastAPI(title="Jeremy – RePut RAG Assistant")

class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    sources: list


@app.get("/health")
def health():
    return {"status": "ok", "bot": "Jeremy", "type": "RAG"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    result = answer_question(req.message)
    return ChatResponse(
        reply=result["answer"],
        sources=result["sources"],
    )
