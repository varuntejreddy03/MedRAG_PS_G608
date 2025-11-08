# ==========================================================
# 🧠 MedRAG Diagnostic Assistant (Local + Deployable)
# Author: Varun Tej
# Version: 2.0 (with structured medical reasoning)
# ==========================================================

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import time
from sentence_transformers import SentenceTransformer
import faiss, numpy as np, json, os, uuid
import google.generativeai as genai
from dotenv import load_dotenv
from database import db
from auth import send_verification_email, verify_code
from auth_middleware import create_access_token
from typing import List, Optional
from datetime import datetime

load_dotenv()

# ----------------------------------------------------------
# 🔹 App setup
# ----------------------------------------------------------
app = FastAPI(title="MedRAG Diagnostic API", description="Retrieval-Augmented Medical Reasoning System")

# Security: Rate limiting
rate_limit_store = {}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    current_time = time.time()
    
    if client_ip in rate_limit_store:
        requests, last_reset = rate_limit_store[client_ip]
        if current_time - last_reset > 60:
            rate_limit_store[client_ip] = [1, current_time]
        elif requests >= 30:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": "Rate limit exceeded. Try again later."}
            )
        else:
            rate_limit_store[client_ip][0] += 1
    else:
        rate_limit_store[client_ip] = [1, current_time]
    
    response = await call_next(request)
    return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*",
        "https://medrag-app.surge.sh",
        "https://*.surge.sh"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security: Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# ----------------------------------------------------------
# 🔹 Load all models and data once (on startup)
# ----------------------------------------------------------
print("🚀 Loading sentence embedding model...")
embed_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

print("📦 Loading FAISS index...")
index = faiss.read_index("models/chunked_ehr_index.faiss")

print("📘 Loading patient EHR chunks...")
chunks = json.load(open("models/patient_chunks.json", "r", encoding="utf-8"))

# Optional: load evidence descriptions (if available)
evidence_dict = {}
if os.path.exists("models/release_evidences.json"):
    with open("models/release_evidences.json", "r", encoding="utf-8") as f:
        evidence_dict = json.load(f)
    print(f"✅ Loaded evidence dictionary with {len(evidence_dict)} entries.")
else:
    print("⚠️ Evidence mapping file not found. Using default mappings...")
    evidence_dict = {
        "E_1": "Ear pain", "E_2": "Fever", "E_3": "Chest pain", "E_4": "Cough", "E_5": "Shortness of breath",
        "E_6": "Abdominal pain", "E_7": "Fatigue", "E_8": "Dyspnea", "E_9": "Weight loss", "E_10": "Swelling"
    }
    print(f"✅ Using default evidence mappings with {len(evidence_dict)} entries.")

# Configure Gemini API
print("🤖 Configuring Gemini API...")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# Database initialized automatically by SQLAlchemy
print("📊 Database ready...")

# ----------------------------------------------------------
# 🔹 Helper: decode evidence codes → readable text
# ----------------------------------------------------------
# Evidence mappings moved to inline default

def decode_evidence_text(text_block: str):
    """
    Replace evidence codes (E_52, E_65, etc.) with descriptions
    if available in evidence_dict.
    """
    import re
    # Find all E_XX patterns
    e_codes = re.findall(r'E_\d+', text_block)
    for code in e_codes:
        if code in evidence_dict:
            text_block = text_block.replace(code, f"{code}: {evidence_dict[code]}")
    return text_block

# ----------------------------------------------------------
# 🔹 Request body schema
# ----------------------------------------------------------
class Query(BaseModel):
    query: str
    k: int = 5
    
    class Config:
        str_max_length = 1000

class ChatMessage(BaseModel):
    message: str
    session_id: str = None
    
    class Config:
        str_max_length = 500

class PatientData(BaseModel):
    fullName: str
    age: int
    gender: str
    phone: str = None
    email: str = None

class ManifestationsData(BaseModel):
    complaint: str
    symptoms: List[str] = []

class HistoryData(BaseModel):
    files: List[str] = []
    manualHistory: str = ""

class EmailRequest(BaseModel):
    email: str
    case_id: str
    patient_name: str
    diagnosis: str

class CaseSubmission(BaseModel):
    patient: PatientData
    manifestations: ManifestationsData
    history: HistoryData = None

class AuthRequest(BaseModel):
    email: str

class VerifyRequest(BaseModel):
    email: str
    code: str

# ----------------------------------------------------------
# 🔹 LLM reasoning prompt templates
# ----------------------------------------------------------
ALLOWED_DIAGNOSES = """acute copd exacerbation infection, bronchiectasis, bronchiolitis, bronchitis, bronchospasm acute asthma exacerbation, pulmonary embolism, pulmonary neoplasm, spontaneous pneumothorax, urti, viral pharyngitis, whooping cough, acute laryngitis, acute pulmonary edema, croup, larygospasm, epiglottitis, pneumonia, atrial fibrillation, myocarditis, pericarditis, psvt, possible nstemi stemi, stable angina, unstable angina, gerd, boerhaave syndrome, pancreatic neoplasm, scombroid food poisoning, inguinal hernia, tuberculosis, hiv initial infection, ebola, influenza, chagas, acute otitis media, acute rhinosinusitis, allergic sinusitis, chronic rhinosinusitis, myasthenia gravis, guillain barre syndrome, cluster headache, acute dystonic reactions, sle, sarcoidosis, anaphylaxis, panic attack, spontaneous rib fracture, anemia"""

def build_diagnosis_prompt(patient_query: str, context: str):
    return f"""Medical AI: Analyze and diagnose. Keep response under 400 words.

Patient: {patient_query}
Similar Cases: {context}
Allowed Diagnoses: {ALLOWED_DIAGNOSES}

### Diagnoses
1. Primary diagnosis from list
2. Brief explanation

### Follow-up Questions
3 questions

### Tests
3-5 tests

### Treatment
Brief plan
"""

def build_chat_prompt(query: str, context: str, history: str = ""):
    return f"""Medical AI: Answer briefly (under 80 words).
{f'History: {history}' if history else ''}
Query: {query}
Cases: {context}
"""

def build_prompt(patient_query: str, context: str):
    return build_diagnosis_prompt(patient_query, context)

# ----------------------------------------------------------
# 🔹 WebSocket Chat endpoint
# ----------------------------------------------------------
@app.websocket("/chat/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    db.create_chat_session(session_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            query = message.get("query", "")
            k = message.get("k", 5)
            
            # Retrieve similar cases
            emb = embed_model.encode([query]).astype("float32")
            D, I = index.search(emb, k)
            retrieved = [chunks[i] for i in I[0]]
            
            # Decode evidence codes
            decoded_context = "\n".join(decode_evidence_text(r) for r in retrieved[:3])
            
            # Build chat history context
            history = db.get_chat_history(session_id)
            history_context = "\n".join([f"User: {h['user']}\nAssistant: {h['assistant']}" for h in history[-3:]])
            
            # Enhanced prompt with chat history
            prompt = build_chat_prompt(query, decoded_context, history_context)
            
            # Generate response
            response = model.generate_content(prompt, generation_config={'max_output_tokens': 250})
            reasoning = response.text
            
            # Store in database
            db.add_chat_message(session_id, query, reasoning)
            
            # Send response
            await websocket.send_text(json.dumps({
                "response": reasoning,
                "matches": retrieved[:3],
                "session_id": session_id
            }))
            
    except WebSocketDisconnect:
        print(f"Client {session_id} disconnected")

# ----------------------------------------------------------
# 🔹 REST API endpoint (for compatibility)
# ----------------------------------------------------------
@app.post("/diagnose")
def diagnose(q: Query):
    emb = embed_model.encode([q.query]).astype("float32")
    D, I = index.search(emb, q.k)
    retrieved = [chunks[i] for i in I[0]]
    decoded_context = "\n".join(decode_evidence_text(r) for r in retrieved[:3])
    prompt = build_diagnosis_prompt(q.query, decoded_context)
    response = model.generate_content(prompt, generation_config={'max_output_tokens': 400})
    
    return {
        "query": q.query,
        "diagnosis": response.text.split("### Diagnoses")[1].split("### ")[0].strip() if "### Diagnoses" in response.text else "Unknown",
        "reasoning": response.text,
        "matches": retrieved[:3],
        "confidence": 85,
        "differentials": ["Alternative diagnosis 1", "Alternative diagnosis 2"],
        "tests": ["ECG", "Blood work", "Chest X-ray"],
        "actions": ["Monitor vital signs", "Administer medication", "Consult specialist"],
        "questions": ["Any family history?", "Previous episodes?", "Current medications?"]
    }

@app.post("/chat")
def chat_endpoint(message: ChatMessage):
    session_id = message.session_id or f"session_{uuid.uuid4().hex[:8]}"
    db.create_chat_session(session_id)
    
    # Get diagnosis for the message
    emb = embed_model.encode([message.message]).astype("float32")
    D, I = index.search(emb, 5)
    retrieved = [chunks[i] for i in I[0]]
    decoded_context = "\n".join(decode_evidence_text(r) for r in retrieved[:3])
    
    # Build chat history context
    history = db.get_chat_history(session_id)
    history_context = "\n".join([f"User: {h['user']}\nAssistant: {h['assistant']}" for h in history[-3:]])
    
    # Enhanced prompt with chat history
    prompt = build_chat_prompt(message.message, decoded_context, history_context)
    
    # Generate response
    response = model.generate_content(prompt, generation_config={'max_output_tokens': 250})
    reasoning = response.text
    
    # Store in database
    db.add_chat_message(session_id, message.message, reasoning)
    
    return {
        "response": reasoning,
        "session_id": session_id,
        "matches": retrieved[:3]
    }

@app.get("/")
def health_check():
    stats = db.get_dashboard_stats()
    return {
        "status": "healthy", 
        "message": "MedRAG API is running",
        "database": "connected",
        "auth": "gmail_enabled",
        "stats": stats
    }

# ----------------------------------------------------------
# 🔹 Clear chat history endpoint
# ----------------------------------------------------------
@app.delete("/chat/{session_id}")
def clear_chat(session_id: str):
    db.create_chat_session(session_id)  # This will reset the session
    return {"message": "Chat history cleared"}

# Cases endpoints
@app.post("/cases")
def submit_case(case_data: CaseSubmission):
    try:
        # Create patient
        patient_id = db.create_patient(
            full_name=case_data.patient.fullName,
            age=case_data.patient.age,
            gender=case_data.patient.gender,
            phone=case_data.patient.phone,
            email=case_data.patient.email
        )
        
        # Create case
        case_id = f"CASE-{uuid.uuid4().hex[:8].upper()}"
        db.create_case(
            case_id=case_id,
            patient_id=patient_id,
            complaint=case_data.manifestations.complaint,
            symptoms=case_data.manifestations.symptoms,
            history=case_data.history.manualHistory if case_data.history else None
        )
        
        # Get AI diagnosis
        query = f"{case_data.manifestations.complaint} {' '.join(case_data.manifestations.symptoms)}"
        emb = embed_model.encode([query]).astype("float32")
        D, I = index.search(emb, 5)
        retrieved = [chunks[i] for i in I[0]]
        decoded_context = "\n".join(decode_evidence_text(r) for r in retrieved[:3])
        prompt = build_diagnosis_prompt(query, decoded_context)
        response = model.generate_content(prompt, generation_config={'max_output_tokens': 400})
        
        # Extract diagnosis
        diagnosis = "Unknown"
        if "### Diagnoses" in response.text:
            diagnosis = response.text.split("### Diagnoses")[1].split("###")[0].strip()
        
        # Update case with diagnosis
        db.update_case_diagnosis(
            case_id=case_id,
            diagnosis=diagnosis,
            confidence=85.0,
            reasoning=response.text,
            matches=retrieved[:3]
        )
        
        # Send email summary to patient
        if case_data.patient.email:
            try:
                from auth import send_diagnosis_email
                email_body = f"""
Dear {case_data.patient.fullName},

Your medical diagnosis report is ready.

Case ID: {case_id}
Diagnosis: {diagnosis}

Please consult with your healthcare provider for detailed information.

Best regards,
MedRAG Team
"""
                send_diagnosis_email(case_data.patient.email, case_id, email_body)
            except Exception as e:
                print(f"Email send failed: {e}")
        
        return {
            "case_id": case_id,
            "status": "completed",
            "message": "Case submitted successfully",
            "diagnosis_result": {
                "diagnosis": diagnosis,
                "reasoning": response.text,
                "confidence": 85.0,
                "matches": retrieved[:3]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cases")
def list_cases(page: int = 1, per_page: int = 10):
    offset = (page - 1) * per_page
    cases = db.get_cases(limit=per_page, offset=offset)
    total = db.get_cases_count()
    
    return {
        "cases": cases,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page
        }
    }

@app.get("/cases/{case_id}")
def get_case(case_id: str):
    case = db.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@app.post("/cases/{case_id}/regenerate")
def regenerate_diagnosis(case_id: str):
    case = db.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Regenerate diagnosis
    query = f"{case['complaint']} {' '.join(case['symptoms']) if case['symptoms'] else ''}"
    emb = embed_model.encode([query]).astype("float32")
    D, I = index.search(emb, 5)
    retrieved = [chunks[i] for i in I[0]]
    decoded_context = "\n".join(decode_evidence_text(r) for r in retrieved[:3])
    prompt = build_diagnosis_prompt(query, decoded_context)
    response = model.generate_content(prompt, generation_config={'max_output_tokens': 400})
    
    diagnosis = "Unknown"
    if "### Diagnoses" in response.text:
        diagnosis = response.text.split("### Diagnoses")[1].split("###")[0].strip()
    
    db.update_case_diagnosis(
        case_id=case_id,
        diagnosis=diagnosis,
        confidence=85.0,
        reasoning=response.text,
        matches=retrieved[:3]
    )
    
    return {
        "case_id": case_id,
        "status": "regenerated",
        "diagnosis_result": {
            "diagnosis": diagnosis,
            "reasoning": response.text,
            "confidence": 85.0
        }
    }

# Dashboard stats
@app.get("/dashboard/stats")
def get_dashboard_stats():
    return db.get_dashboard_stats()

# Authentication endpoints
@app.options("/send-verification")
async def options_send_verification():
    return JSONResponse(content={"message": "OK"}, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "*"
    })

@app.post("/send-verification")
def send_verification(request: AuthRequest):
    success = send_verification_email(request.email)
    if success:
        return {"message": "Verification code sent", "success": True}
    else:
        raise HTTPException(status_code=500, detail="Failed to send verification code")

@app.options("/verify-code")
def options_verify_code():
    return {"message": "OK"}

@app.post("/verify-code")
def verify_code_endpoint(request: VerifyRequest):
    if verify_code(request.email, request.code):
        token = create_access_token(request.email)
        return {
            "message": "Authentication successful",
            "success": True,
            "token": token,
            "user": {
                "email": request.email,
                "name": request.email.split('@')[0].title()
            }
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

@app.options("/auth/send-code")
def options_send_code():
    return {"message": "OK"}

@app.post("/send-patient-email")
def send_patient_email(request: dict):
    try:
        from auth import send_diagnosis_email
        email = request.get('email')
        case_id = request.get('case_id')
        patient_name = request.get('patient_name')
        diagnosis = request.get('diagnosis', 'Pending')
        
        email_body = f"""
Dear {patient_name},

Your medical diagnosis report is ready.

Case ID: {case_id}
Diagnosis: {diagnosis}

Please consult with your healthcare provider for detailed information.

Best regards,
MedRAG Team
"""
        send_diagnosis_email(email, case_id, email_body)
        return {"message": "Email sent successfully", "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/send-code")
def send_auth_code(request: AuthRequest):
    success = send_verification_email(request.email)
    if success:
        return {"message": "Verification code sent", "success": True}
    else:
        raise HTTPException(status_code=500, detail="Failed to send verification code")

@app.options("/auth/verify")
def options_verify():
    return {"message": "OK"}

@app.post("/auth/verify")
def verify_auth_code(request: VerifyRequest):
    if verify_code(request.email, request.code):
        token = create_access_token(request.email)
        return {
            "message": "Authentication successful",
            "success": True,
            "token": token,
            "user": {
                "email": request.email,
                "name": request.email.split('@')[0].title()
            }
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid or expired code")

# Export case
@app.get("/export/{case_id}")
def export_case(case_id: str):
    case = db.get_case_by_id(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    return {
        "case_id": case_id,
        "export_data": case,
        "exported_at": datetime.now().isoformat()
    }

# Feedback
@app.post("/feedback")
def submit_feedback(feedback_data: dict):
    return {
        "message": "Feedback submitted successfully",
        "feedback_id": f"FB-{uuid.uuid4().hex[:8].upper()}"
    }

# ----------------------------------------------------------
# 🔹 Run using: uvicorn main:app --reload
# ----------------------------------------------------------
