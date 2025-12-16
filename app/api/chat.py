"""Chat API endpoints for diagnosis follow-up conversations."""

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user_model import User
from ..services.rag_engine import rag_engine
from ..services.faiss_loader import faiss_loader
import json

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    diagnosis_id: int
    message: str

class ChatResponse(BaseModel):
    response: str
    similar_cases: List[str] = []

# In-memory chat history (use Redis in production)
chat_sessions = {}

@router.post("/", response_model=ChatResponse)
async def chat_with_diagnosis(
    request: ChatRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat about a specific diagnosis with RAG context."""
    from ..models.patient_model import Patient
    
    # Get diagnosis
    user = db.query(User).filter(User.email == current_user).first()
    diagnosis = db.query(Patient).filter(
        Patient.id == request.diagnosis_id,
        Patient.user_id == user.id
    ).first()
    
    if not diagnosis:
        return ChatResponse(response="Diagnosis not found.", similar_cases=[])
    
    # Build context from diagnosis
    context = f"""
    Patient: {diagnosis.age}y {diagnosis.gender}
    Symptoms: {diagnosis.symptoms}
    History: {diagnosis.medical_history}
    Diagnosis: {diagnosis.diagnosis}
    """
    
    # Get chat history for this diagnosis
    session_key = f"{current_user}_{request.diagnosis_id}"
    if session_key not in chat_sessions:
        chat_sessions[session_key] = []
    
    history = chat_sessions[session_key][-3:]  # Last 3 messages
    history_text = "\n".join([f"User: {h['user']}\nAssistant: {h['assistant']}" for h in history])
    
    # Search FAISS for relevant cases
    query_vector = rag_engine.encoder.encode([request.message]).astype('float32')
    similar_cases = faiss_loader.search(query_vector, k=3)
    cases_text = "\n".join([case["text"] for case in similar_cases])
    
    # Generate response
    full_context = f"{context}\n\nSimilar Cases:\n{cases_text}\n\nChat History:\n{history_text}"
    response = rag_engine.chat_response(request.message, full_context)
    
    # Store in history
    chat_sessions[session_key].append({
        "user": request.message,
        "assistant": response
    })
    
    return ChatResponse(
        response=response,
        similar_cases=[case["text"][:100] + "..." for case in similar_cases]
    )

@router.delete("/{diagnosis_id}")
async def clear_chat_history(
    diagnosis_id: int,
    current_user: str = Depends(get_current_user)
):
    """Clear chat history for a diagnosis."""
    session_key = f"{current_user}_{diagnosis_id}"
    if session_key in chat_sessions:
        del chat_sessions[session_key]
    return {"message": "Chat history cleared"}

@router.websocket("/ws/{diagnosis_id}")
async def websocket_chat(websocket: WebSocket, diagnosis_id: int):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message = message_data.get("message", "")
            
            # Get similar cases
            query_vector = rag_engine.encoder.encode([message]).astype('float32')
            similar_cases = faiss_loader.search(query_vector, k=3)
            cases_text = "\n".join([case["text"] for case in similar_cases])
            
            # Generate response
            response = rag_engine.chat_response(message, cases_text)
            
            await websocket.send_text(json.dumps({
                "response": response,
                "similar_cases": [case["text"][:100] for case in similar_cases]
            }))
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for diagnosis {diagnosis_id}")
