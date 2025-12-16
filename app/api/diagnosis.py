"""Diagnosis API endpoints for patient case submission and retrieval."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List
from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user_model import User
from ..models.patient_model import Patient
from ..services.rag_engine import rag_engine
from ..services.email_service import email_service

router = APIRouter(prefix="/diagnosis", tags=["diagnosis"])

class DiagnosisRequest(BaseModel):
    """Request model for diagnosis submission."""
    patient_name: str = Field(..., min_length=1, description="Patient name")
    patient_email: str = Field(..., min_length=1, description="Patient email")
    age: int = Field(..., ge=0, le=150, description="Patient age")
    gender: str = Field(..., min_length=1, description="Patient gender")
    symptoms: str = Field(..., min_length=1, description="Patient symptoms")
    medical_history: str = Field("", description="Patient medical history")

class DiagnosisResponse(BaseModel):
    """Response model for diagnosis data."""
    id: int
    patient_name: str = ""
    patient_email: str = ""
    age: int
    gender: str
    symptoms: str
    medical_history: str
    diagnosis: str
    confidence_score: str
    created_at: str
    
    class Config:
        from_attributes = True

@router.post("/", response_model=dict)
async def create_diagnosis(
    request: DiagnosisRequest,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new diagnosis for a patient case."""
    # Get user
    user = db.query(User).filter(User.email == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Generate diagnosis using RAG
    result = rag_engine.generate_diagnosis(
        symptoms=request.symptoms,
        age=request.age,
        gender=request.gender,
        medical_history=request.medical_history
    )
    
    # Save to database
    patient = Patient(
        user_id=user.id,
        patient_name=request.patient_name,
        patient_email=request.patient_email,
        age=request.age,
        gender=request.gender,
        symptoms=request.symptoms,
        medical_history=request.medical_history,
        diagnosis=result["diagnosis"],
        confidence_score=result["confidence"]
    )
    
    db.add(patient)
    db.commit()
    db.refresh(patient)
    
    # Send diagnosis report to patient email
    try:
        email_body = f"""
Dear {request.patient_name},

Your medical diagnosis report is ready.

Patient Information:
- Name: {request.patient_name}
- Age: {request.age} years
- Gender: {request.gender}

Symptoms: {request.symptoms}

Diagnosis:
{result['diagnosis']}

Confidence: {result['confidence']}

Please consult with your healthcare provider for detailed information and treatment plan.

Best regards,
MedRAG Medical Team
"""
        email_service.send_diagnosis_notification(request.patient_email, email_body)
    except Exception as e:
        print(f"Email send failed: {e}")
    
    faiss_info = result.get("faiss_retrieval", {})
    print(f"✅ Diagnosis created with FAISS retrieval: {faiss_info}")
    
    return {
        "id": patient.id,
        "diagnosis": result["diagnosis"],
        "confidence": result["confidence"],
        "similar_cases_found": result["similar_cases"],
        "faiss_retrieval": faiss_info,
        "model_used": result.get("model_used", "gemini-2.5-flash"),
        "email_sent": True,
        "patient_email": request.patient_email,
        "rag_info": f"FAISS retrieved {faiss_info.get('cases_found', 0)} similar cases with top similarity: {faiss_info.get('top_similarity', 0):.4f}"
    }

@router.get("/", response_model=List[DiagnosisResponse])
async def get_user_diagnoses(
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all diagnoses for the current user."""
    user = db.query(User).filter(User.email == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    patients = db.query(Patient).filter(Patient.user_id == user.id).all()
    return [{**p.__dict__, "created_at": p.created_at.isoformat()} for p in patients]

@router.get("/{diagnosis_id}", response_model=DiagnosisResponse)
async def get_diagnosis(
    diagnosis_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific diagnosis by ID for the current user."""
    user = db.query(User).filter(User.email == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    patient = db.query(Patient).filter(
        Patient.id == diagnosis_id,
        Patient.user_id == user.id
    ).first()
    
    if not patient:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    
    return {**patient.__dict__, "created_at": patient.created_at.isoformat()}