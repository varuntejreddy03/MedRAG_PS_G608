from fastapi import APIRouter, Depends
from pydantic import BaseModel
from ..core.security import get_current_user
from ..services.rag_engine import rag_engine

router = APIRouter(prefix="/rag", tags=["rag"])

class ChatRequest(BaseModel):
    message: str
    context: str = ""

class ChatResponse(BaseModel):
    response: str

class DiagnosisQuery(BaseModel):
    symptoms: str
    age: int
    gender: str
    medical_history: str = ""

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: str = Depends(get_current_user)
):
    response = rag_engine.chat_response(request.message, request.context)
    return ChatResponse(response=response)

@router.post("/quick-diagnosis")
async def quick_diagnosis(
    request: DiagnosisQuery,
    current_user: str = Depends(get_current_user)
):
    result = rag_engine.generate_diagnosis(
        symptoms=request.symptoms,
        age=request.age,
        gender=request.gender,
        medical_history=request.medical_history
    )
    return result

@router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "RAG Engine"}