# MedRAG Architecture and Flow Diagrams

This document provides detailed visual representations of the MedRAG system architecture and data flows.

## Table of Contents
1. [High-Level System Architecture](#high-level-system-architecture)
2. [Authentication Flow](#authentication-flow)
3. [Case Submission Flow](#case-submission-flow)
4. [RAG Diagnosis Flow](#rag-diagnosis-flow)
5. [Chat Interface Flow](#chat-interface-flow)
6. [Database Schema](#database-schema)
7. [Deployment Architecture](#deployment-architecture)
8. [Request/Response Flow](#requestresponse-flow)

---

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              Next.js 14 Frontend (Vercel)                   │   │
│  │                                                             │   │
│  │  • Landing Page / Login                                    │   │
│  │  • Clinical Wizard (Multi-step Form)                       │   │
│  │  • Dashboard (Analytics & Case Management)                 │   │
│  │  • Chat Interface (Real-time Messaging)                    │   │
│  │  • Diagnostic Results Display                              │   │
│  └────────────────────────────────────────────────────────────┘   │
│                              ↕ HTTPS                               │
└─────────────────────────────────────────────────────────────────────┘
                               ↕
┌─────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                              │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │           FastAPI Backend (AWS EC2)                        │   │
│  │                                                            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │   Auth       │  │   Diagnosis  │  │    Chat      │   │   │
│  │  │   Module     │  │   Module     │  │    Module    │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  │                                                            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │    Case      │  │   Dashboard  │  │    Email     │   │   │
│  │  │  Management  │  │    Stats     │  │    Service   │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  │                                                            │   │
│  │  ┌─────────────────────────────────────────────────┐     │   │
│  │  │        AI & Vector Search Engine                │     │   │
│  │  │  • Sentence Transformers (Embeddings)           │     │   │
│  │  │  • FAISS Vector Index (17K+ cases)             │     │   │
│  │  │  • Google Gemini 2.0 (LLM)                     │     │   │
│  │  └─────────────────────────────────────────────────┘     │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
         ↕                    ↕                    ↕
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│  PostgreSQL     │  │    AWS S3        │  │  Gmail SMTP     │
│  (AWS RDS)      │  │    Bucket        │  │  Server         │
│                 │  │                  │  │                 │
│  • Patients     │  │  • FAISS Index  │  │  • Verification │
│  • Cases        │  │    (4.4GB)      │  │    Codes        │
│  • Chat         │  │  • Patient      │  │  • Diagnosis    │
│    Sessions     │  │    Chunks JSON  │  │    Reports      │
│                 │  │  • Evidence     │  │                 │
│                 │  │    Dictionary   │  │                 │
└─────────────────┘  └──────────────────┘  └─────────────────┘
```

---

## Authentication Flow

```
┌──────────┐                                                      ┌──────────┐
│  User    │                                                      │ Backend  │
└────┬─────┘                                                      └────┬─────┘
     │                                                                 │
     │ 1. Navigate to Landing Page                                    │
     ├────────────────────────────────────────────────────────────────┤
     │                                                                 │
     │ 2. Enter Email Address                                         │
     ├──────────────────────────────────────────────────────────────► │
     │            POST /send-verification                              │
     │            { "email": "user@example.com" }                      │
     │                                                                 │
     │                                    3. Generate 6-digit code     │
     │                                       Store in memory cache     │
     │                                       Set 10-min expiration     │
     │                                                                 │
     │                                    4. Send email via Gmail SMTP │
     │                                       ├─────────────────────────┤
     │                                       │    Gmail Server         │
     │                                       └─────────────────────────┤
     │                                                                 │
     │ ◄────────────────────────────────────────────────────────────── │
     │         Response: { "success": true,                            │
     │                     "message": "Code sent" }                    │
     │                                                                 │
     │ 5. Check email and enter code                                  │
     │                                                                 │
     │ 6. Submit verification code                                    │
     ├──────────────────────────────────────────────────────────────► │
     │            POST /verify-code                                    │
     │            { "email": "user@example.com",                       │
     │              "code": "123456" }                                 │
     │                                                                 │
     │                                    7. Validate code             │
     │                                       Check expiration          │
     │                                       Generate JWT token        │
     │                                       (30-min expiry)           │
     │                                                                 │
     │ ◄────────────────────────────────────────────────────────────── │
     │         Response: {                                             │
     │           "success": true,                                      │
     │           "token": "eyJhbGc...",                                │
     │           "user": {                                             │
     │             "email": "user@example.com",                        │
     │             "name": "User"                                      │
     │           }                                                     │
     │         }                                                       │
     │                                                                 │
     │ 8. Store token in localStorage                                 │
     │    Set session expiry (30 minutes)                             │
     │    Redirect to Dashboard                                       │
     │                                                                 │
     │ 9. All subsequent requests include token                       │
     ├──────────────────────────────────────────────────────────────► │
     │            Authorization: Bearer eyJhbGc...                     │
     │                                                                 │
     │                                   10. Validate token on each    │
     │                                       request (middleware)      │
     │                                                                 │
     │ 11. After 30 minutes: Token expires                            │
     │     Auto-logout, clear localStorage                            │
     │     Redirect to login                                          │
     │                                                                 │
```

---

## Case Submission Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                    CLINICAL WIZARD - FRONTEND                        │
└──────────────────────────────────────────────────────────────────────┘
                            ↓
    ┌───────────────────────────────────────────────────┐
    │  Step 1: Patient Information                      │
    │  • Full Name                                      │
    │  • Age                                            │
    │  • Gender                                         │
    │  • Phone (optional)                               │
    │  • Email (optional)                               │
    └───────────────┬───────────────────────────────────┘
                    ↓
    ┌───────────────────────────────────────────────────┐
    │  Step 2: Manifestations                           │
    │  • Chief Complaint (free text)                    │
    │  • Symptoms (checkbox selection)                  │
    │    - Fever, Cough, Chest pain, etc.              │
    └───────────────┬───────────────────────────────────┘
                    ↓
    ┌───────────────────────────────────────────────────┐
    │  Step 3: Medical History (Optional)               │
    │  • Upload files (lab results, reports)            │
    │  • Manual history text input                      │
    └───────────────┬───────────────────────────────────┘
                    ↓
    ┌───────────────────────────────────────────────────┐
    │  Submit → POST /cases                             │
    └───────────────┬───────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────────────────────────────┐
│                      BACKEND PROCESSING                              │
│                                                                      │
│  1. Create Patient Record                                           │
│     ┌─────────────────────────────────────┐                        │
│     │ INSERT INTO patients                 │                        │
│     │ (full_name, age, gender, email...)   │                        │
│     │ RETURNING patient_id                 │                        │
│     └─────────────────┬───────────────────┘                        │
│                       ↓                                              │
│  2. Generate Case ID                                                │
│     ┌─────────────────────────────────────┐                        │
│     │ case_id = "CASE-" + uuid[:8].upper()│                        │
│     │ Example: CASE-A3F9B27E               │                        │
│     └─────────────────┬───────────────────┘                        │
│                       ↓                                              │
│  3. Create Case Record                                              │
│     ┌─────────────────────────────────────┐                        │
│     │ INSERT INTO cases                    │                        │
│     │ (id, patient_id, complaint,          │                        │
│     │  symptoms, history, status='pending')│                        │
│     └─────────────────┬───────────────────┘                        │
│                       ↓                                              │
│  4. RAG Diagnosis Process (see detailed flow below)                │
│     ┌─────────────────────────────────────┐                        │
│     │ • Embed query                        │                        │
│     │ • Search FAISS index                 │                        │
│     │ • Retrieve similar cases             │                        │
│     │ • Generate diagnosis with Gemini     │                        │
│     └─────────────────┬───────────────────┘                        │
│                       ↓                                              │
│  5. Update Case with Diagnosis                                      │
│     ┌─────────────────────────────────────┐                        │
│     │ UPDATE cases                         │                        │
│     │ SET diagnosis = '...',               │                        │
│     │     confidence = 85.0,               │                        │
│     │     reasoning = '...',               │                        │
│     │     matches = [...],                 │                        │
│     │     status = 'diagnosed'             │                        │
│     │ WHERE id = case_id                   │                        │
│     └─────────────────┬───────────────────┘                        │
│                       ↓                                              │
│  6. Send Email to Patient (if email provided)                      │
│     ┌─────────────────────────────────────┐                        │
│     │ Gmail SMTP Server                    │                        │
│     │ Subject: "Diagnosis Report - CASE-X" │                        │
│     │ Body: Case ID, Diagnosis summary     │                        │
│     └─────────────────┬───────────────────┘                        │
│                       ↓                                              │
│  7. Return Response                                                 │
│     ┌─────────────────────────────────────┐                        │
│     │ {                                    │                        │
│     │   "case_id": "CASE-A3F9B27E",       │                        │
│     │   "status": "completed",             │                        │
│     │   "diagnosis_result": {              │                        │
│     │     "diagnosis": "...",              │                        │
│     │     "reasoning": "...",              │                        │
│     │     "confidence": 85.0,              │                        │
│     │     "matches": [...]                 │                        │
│     │   }                                  │                        │
│     │ }                                    │                        │
│     └──────────────────────────────────────┘                        │
└──────────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    FRONTEND - DISPLAY RESULTS                        │
│  • Show diagnosis with confidence score                              │
│  • Display clinical reasoning                                        │
│  • List follow-up questions                                          │
│  • Recommend diagnostic tests                                        │
│  • Suggest treatment plan                                            │
│  • Show similar cases that informed the diagnosis                    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## RAG Diagnosis Flow

This is the core AI diagnosis process using Retrieval-Augmented Generation:

```
┌─────────────────────────────────────────────────────────────────────┐
│                INPUT: Patient Query                                  │
│  "30 year old male with chest pain and shortness of breath"         │
└────────────────────────────┬────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: Text Embedding                                             │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Sentence Transformer Model                                 │    │
│  │  (all-MiniLM-L6-v2)                                         │    │
│  │                                                             │    │
│  │  Input Text → 384-dimensional vector                        │    │
│  │  [0.234, -0.891, 0.456, ..., 0.123]                        │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2: Vector Similarity Search                                   │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  FAISS Index (17,000+ patient cases)                        │    │
│  │                                                             │    │
│  │  query_vector ─────► K-Nearest Neighbors Search            │    │
│  │                      k = 5 (top 5 matches)                  │    │
│  │                                                             │    │
│  │  Returns:                                                   │    │
│  │  • Indices: [1523, 8942, 3211, 9876, 4455]                │    │
│  │  • Distances: [0.12, 0.15, 0.18, 0.21, 0.24]              │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3: Retrieve Case Texts                                        │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  patient_chunks.json                                        │    │
│  │                                                             │    │
│  │  chunks[1523]: "45yo male, acute chest pain, elevated      │    │
│  │                 troponin, ECG changes → MI"                 │    │
│  │                                                             │    │
│  │  chunks[8942]: "32yo male, chest pain radiating to arm,    │    │
│  │                 normal ECG → anxiety disorder"              │    │
│  │                                                             │    │
│  │  chunks[3211]: "28yo female, chest pain with shortness     │    │
│  │                 of breath → pulmonary embolism"             │    │
│  │                                                             │    │
│  │  ... (top 3-5 cases selected)                              │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4: Decode Evidence Codes                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Evidence Dictionary (release_evidences.json)               │    │
│  │                                                             │    │
│  │  Replace: "E_52" → "Chest pain"                            │    │
│  │  Replace: "E_65" → "Shortness of breath"                   │    │
│  │  Replace: "E_14" → "Palpitations"                          │    │
│  │                                                             │    │
│  │  Enhanced Context: Human-readable medical terms             │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 5: Build LLM Prompt                                           │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ Medical AI: Analyze and diagnose.                          │    │
│  │                                                             │    │
│  │ Patient: 30yo male with chest pain and SOB                 │    │
│  │                                                             │    │
│  │ Similar Cases:                                              │    │
│  │ 1. 45yo male, acute chest pain, elevated troponin → MI     │    │
│  │ 2. 32yo male, chest pain, normal ECG → anxiety             │    │
│  │ 3. 28yo female, chest pain, SOB → PE                       │    │
│  │                                                             │    │
│  │ Allowed Diagnoses:                                          │    │
│  │ acute copd exacerbation, bronchitis, pneumonia,            │    │
│  │ myocarditis, NSTEMI, STEMI, pulmonary embolism,           │    │
│  │ panic attack, anemia... [full list]                        │    │
│  │                                                             │    │
│  │ Please provide:                                             │    │
│  │ 1. Primary diagnosis from allowed list                      │    │
│  │ 2. Clinical reasoning                                       │    │
│  │ 3. Follow-up questions (3)                                  │    │
│  │ 4. Recommended tests (3-5)                                  │    │
│  │ 5. Treatment plan                                           │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 6: LLM Generation                                             │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Google Gemini 2.0 Flash                                    │    │
│  │  max_output_tokens: 400                                     │    │
│  │                                                             │    │
│  │  Generates structured response:                             │    │
│  │                                                             │    │
│  │  ### Diagnoses                                              │    │
│  │  1. Possible NSTEMI (Non-ST Elevation Myocardial           │    │
│  │     Infarction)                                             │    │
│  │  2. Given the patient's age, gender, and presenting        │    │
│  │     symptoms of chest pain and shortness of breath,         │    │
│  │     combined with similar cases showing cardiac events,     │    │
│  │     an acute coronary syndrome should be ruled out.         │    │
│  │                                                             │    │
│  │  ### Follow-up Questions                                    │    │
│  │  1. Is the chest pain radiating to the arm or jaw?         │    │
│  │  2. Any family history of heart disease?                   │    │
│  │  3. Are you experiencing nausea or sweating?               │    │
│  │                                                             │    │
│  │  ### Tests                                                  │    │
│  │  1. ECG (immediate)                                         │    │
│  │  2. Troponin levels                                         │    │
│  │  3. Complete blood count                                    │    │
│  │  4. Chest X-ray                                             │    │
│  │  5. D-dimer (rule out PE)                                   │    │
│  │                                                             │    │
│  │  ### Treatment                                              │    │
│  │  Immediate: Aspirin, oxygen if needed, monitor vitals.     │    │
│  │  Admit for observation and cardiac workup.                 │    │
│  └────────────────────────────────────────────────────────────┘    │
└────────────────────────────┬────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────────┐
│  OUTPUT: Structured Diagnosis Response                              │
│  • Primary diagnosis                                                │
│  • Clinical reasoning                                               │
│  • Confidence score: 85%                                            │
│  • Similar cases used                                               │
│  • Follow-up questions                                              │
│  • Recommended tests                                                │
│  • Treatment plan                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Chat Interface Flow

```
┌──────────┐                                              ┌──────────┐
│  User    │                                              │ Backend  │
└────┬─────┘                                              └────┬─────┘
     │                                                          │
     │ 1. Open Chat Interface                                  │
     │    WebSocket Connection: ws://backend/chat/{session_id} │
     ├────────────────────────────────────────────────────────►│
     │                                                          │
     │                                2. Create chat session    │
     │                                   in database            │
     │                                   session_id stored      │
     │                                                          │
     │ ◄────────────────────────────────────────────────────────│
     │         Connection established                           │
     │                                                          │
     │ 3. User types message                                   │
     │    "What could cause my symptoms?"                      │
     ├────────────────────────────────────────────────────────►│
     │         WebSocket message                                │
     │         { "query": "...", "k": 5 }                      │
     │                                                          │
     │                                4. Process message:       │
     │                                   ┌─────────────────┐   │
     │                                   │ Embed query      │   │
     │                                   └────────┬────────┘   │
     │                                            ↓             │
     │                                   ┌─────────────────┐   │
     │                                   │ Search FAISS    │   │
     │                                   │ (get top 5)     │   │
     │                                   └────────┬────────┘   │
     │                                            ↓             │
     │                                   ┌─────────────────┐   │
     │                                   │ Retrieve cases  │   │
     │                                   └────────┬────────┘   │
     │                                            ↓             │
     │                                   ┌─────────────────┐   │
     │                                   │ Get chat        │   │
     │                                   │ history (last 3)│   │
     │                                   └────────┬────────┘   │
     │                                            ↓             │
     │                                   ┌─────────────────┐   │
     │                                   │ Build prompt    │   │
     │                                   │ with context    │   │
     │                                   └────────┬────────┘   │
     │                                            ↓             │
     │                                   ┌─────────────────┐   │
     │                                   │ Call Gemini     │   │
     │                                   │ (max 250 tokens)│   │
     │                                   └────────┬────────┘   │
     │                                            ↓             │
     │                                   ┌─────────────────┐   │
     │                                   │ Store in        │   │
     │                                   │ chat_sessions   │   │
     │                                   └─────────────────┘   │
     │                                                          │
     │ ◄────────────────────────────────────────────────────────│
     │         Response via WebSocket                           │
     │         {                                                │
     │           "response": "Based on your symptoms...",       │
     │           "matches": [...],                              │
     │           "session_id": "session_abc123"                 │
     │         }                                                │
     │                                                          │
     │ 5. Display response in chat bubble                      │
     │                                                          │
     │ 6. User continues conversation                          │
     │    "Should I be worried?"                               │
     ├────────────────────────────────────────────────────────►│
     │                                                          │
     │                                7. Process with          │
     │                                   previous context      │
     │                                   (chat history)        │
     │                                                          │
     │ ◄────────────────────────────────────────────────────────│
     │         Contextual response                              │
     │                                                          │
     │ 8. Disconnect or timeout (30 minutes)                   │
     ├────────────────────────────────────────────────────────►│
     │         WebSocket close                                  │
     │                                                          │
     │                                9. Session remains in DB  │
     │                                   for history            │
     │                                                          │
```

---

## Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                         PATIENTS                                │
├─────────────────────────────────────────────────────────────────┤
│  id              INTEGER         PRIMARY KEY, AUTO_INCREMENT    │
│  full_name       VARCHAR(255)    NOT NULL                       │
│  age             INTEGER          NOT NULL                       │
│  gender          VARCHAR(50)      NOT NULL                       │
│  phone           VARCHAR(20)      NULLABLE                       │
│  email           VARCHAR(255)     NULLABLE                       │
│  created_at      TIMESTAMP        DEFAULT NOW()                 │
└─────────────────────────────────────────────────────────────────┘
                        │
                        │ 1:N
                        ↓
┌─────────────────────────────────────────────────────────────────┐
│                          CASES                                  │
├─────────────────────────────────────────────────────────────────┤
│  id              VARCHAR(50)      PRIMARY KEY (CASE-XXXXXXXX)   │
│  patient_id      INTEGER          FOREIGN KEY → patients.id     │
│  complaint       TEXT             NOT NULL                       │
│  symptoms        TEXT (JSON)      NOT NULL                       │
│  history         TEXT             NULLABLE                       │
│  diagnosis       TEXT             NULLABLE                       │
│  confidence      FLOAT            NULLABLE (0-100)               │
│  status          VARCHAR(20)      DEFAULT 'pending'              │
│                                   ('pending' | 'diagnosed')      │
│  reasoning       TEXT             NULLABLE (full AI response)    │
│  matches         TEXT (JSON)      NULLABLE (similar cases)       │
│  created_at      TIMESTAMP        DEFAULT NOW()                 │
│  updated_at      TIMESTAMP        DEFAULT NOW(), ON UPDATE      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     CHAT_SESSIONS                               │
├─────────────────────────────────────────────────────────────────┤
│  id              VARCHAR(50)      PRIMARY KEY (session_XXXX)    │
│  messages        TEXT (JSON)      [                             │
│                                     {                            │
│                                       "user": "...",             │
│                                       "assistant": "...",        │
│                                       "timestamp": "..."         │
│                                     }                            │
│                                   ]                              │
│  created_at      TIMESTAMP        DEFAULT NOW()                 │
│  updated_at      TIMESTAMP        DEFAULT NOW(), ON UPDATE      │
└─────────────────────────────────────────────────────────────────┘

Indexes:
  - patients(id) - PRIMARY KEY
  - cases(id) - PRIMARY KEY
  - cases(patient_id) - FOREIGN KEY INDEX
  - cases(created_at) - For sorting/filtering
  - chat_sessions(id) - PRIMARY KEY
```

---

## Deployment Architecture

### Production Setup (AWS)

```
                            ┌──────────────────────┐
                            │   Route 53 (DNS)     │
                            │  medrag.example.com  │
                            └──────────┬───────────┘
                                       │
                            ┌──────────▼───────────┐
                            │  CloudFront (CDN)    │
                            │  SSL/TLS Certificate │
                            └──────────┬───────────┘
                                       │
              ┌────────────────────────┴────────────────────────┐
              │                                                  │
    ┌─────────▼────────┐                           ┌────────────▼──────────┐
    │  Vercel (CDN)    │                           │   EC2 Instance        │
    │  Next.js Frontend│                           │   Ubuntu 22.04        │
    │  • Static Assets │                           │   t3.large (8GB RAM)  │
    │  • SSR Pages     │                           │                       │
    │  • Edge Functions│◄─────── HTTPS ──────────►│   FastAPI Backend     │
    └──────────────────┘                           │   • Uvicorn Server    │
                                                    │   • Python 3.10+      │
                                                    │                       │
                                                    │   Systemd Service     │
                                                    │   /etc/systemd/...    │
                                                    └────────┬──────────────┘
                                                             │
                                    ┌────────────────────────┼────────────────────────┐
                                    │                        │                        │
                        ┌───────────▼──────────┐  ┌──────────▼──────────┐  ┌─────────▼────────┐
                        │  AWS RDS             │  │  AWS S3 Bucket      │  │  Gmail SMTP      │
                        │  PostgreSQL 15       │  │                     │  │  smtp.gmail.com  │
                        │  db.t3.micro         │  │  medrag-data-bucket │  │  Port 587 (TLS)  │
                        │                      │  │                     │  │                  │
                        │  • patients table    │  │  Model Files:       │  │  • Verification  │
                        │  • cases table       │  │  • faiss index      │  │    codes         │
                        │  • chat_sessions     │  │    (4.4GB)          │  │  • Diagnosis     │
                        │                      │  │  • chunks.json      │  │    reports       │
                        │  Automated backups   │  │  • evidences.json   │  │                  │
                        │  Multi-AZ deployment │  │                     │  │                  │
                        └──────────────────────┘  │  Versioning enabled │  └──────────────────┘
                                                   │  Lifecycle policies │
                                                   └─────────────────────┘

Security Groups:
  EC2:
    - Port 22 (SSH) - Admin IP only
    - Port 8000 (HTTP) - 0.0.0.0/0
    - Port 443 (HTTPS) - 0.0.0.0/0 (if Nginx)

  RDS:
    - Port 5432 (PostgreSQL) - EC2 security group only

  S3:
    - IAM role-based access
    - Bucket policy for EC2 instance
```

### Development Setup (Local)

```
┌────────────────────────────────────────────────────────────────┐
│  Developer Machine                                             │
│                                                                 │
│  ┌─────────────────┐              ┌─────────────────┐         │
│  │  Frontend       │              │  Backend        │         │
│  │  localhost:3000 │◄── HTTP ───►│  localhost:8000 │         │
│  │                 │              │                 │         │
│  │  npm run dev    │              │  uvicorn main   │         │
│  │  Next.js        │              │  --reload       │         │
│  └─────────────────┘              └────────┬────────┘         │
│                                             │                   │
│                                    ┌────────▼────────┐         │
│                                    │  SQLite         │         │
│                                    │  medrag.db      │         │
│                                    │  (local file)   │         │
│                                    └─────────────────┘         │
│                                                                 │
│  Models stored locally in /backend/models/                     │
│  - chunked_ehr_index.faiss                                     │
│  - patient_chunks.json                                         │
│  - release_evidences.json                                      │
└────────────────────────────────────────────────────────────────┘
```

---

## Request/Response Flow

### Example: Complete Diagnosis Request

```
1. Client Request
   ↓
   POST https://api.medrag.com/cases
   Headers:
     Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
     Content-Type: application/json
   Body:
     {
       "patient": {
         "fullName": "John Doe",
         "age": 45,
         "gender": "Male",
         "email": "john@example.com"
       },
       "manifestations": {
         "complaint": "Severe chest pain",
         "symptoms": ["Chest pain", "Shortness of breath", "Sweating"]
       },
       "history": {
         "manualHistory": "Smoker for 20 years, family history of heart disease"
       }
     }

2. API Gateway (Rate Limiting)
   ↓
   • Check client IP
   • Increment request counter
   • If > 30 requests/min → 429 Too Many Requests
   • If OK → Continue

3. Authentication Middleware
   ↓
   • Extract Bearer token
   • Verify JWT signature
   • Check expiration
   • If invalid → 401 Unauthorized
   • If valid → Continue

4. Request Validation (Pydantic)
   ↓
   • Validate schema
   • Check required fields
   • Validate data types
   • Check string lengths
   • If invalid → 422 Validation Error
   • If valid → Continue

5. Database Operations
   ↓
   • BEGIN TRANSACTION
   • INSERT INTO patients (...)
   • INSERT INTO cases (...)
   • COMMIT

6. AI Processing Pipeline
   ↓
   Embed Query
     ↓
   Search FAISS (5ms)
     ↓
   Retrieve Cases (10ms)
     ↓
   Decode Evidence (5ms)
     ↓
   Call Gemini API (1-3 seconds)
     ↓
   Parse Response

7. Update Database
   ↓
   • UPDATE cases SET diagnosis=..., status='diagnosed'

8. Send Email (Async)
   ↓
   • Connect to Gmail SMTP
   • Send diagnosis report
   • (Non-blocking)

9. Format Response
   ↓
   {
     "case_id": "CASE-A3F9B27E",
     "status": "completed",
     "message": "Case submitted successfully",
     "diagnosis_result": {
       "diagnosis": "Possible NSTEMI",
       "reasoning": "### Diagnoses\n1. Possible NSTEMI...",
       "confidence": 85.0,
       "matches": [
         "45yo male, chest pain, elevated troponin → MI",
         "50yo male, chest pain, ECG changes → unstable angina",
         "42yo male, chest pain, sweating → acute MI"
       ]
     }
   }

10. Return to Client
    ↓
    HTTP 200 OK
    Content-Type: application/json
    Response body (see above)

Total Time: ~2-4 seconds
```

---

## Performance Metrics

### Response Times (Typical)
- Authentication: ~500ms (including email send time 200-400ms)
- Case submission: ~2-4 seconds
  - Database: 50-100ms
  - Embedding: 10-20ms
  - FAISS search: 5-10ms
  - Gemini API: 1-3 seconds
  - Email: 200-400ms (async, non-blocking)
- Chat message: ~1-2 seconds
- Dashboard load: ~100-200ms

### Scalability Considerations
- **FAISS Search**: O(log n) complexity, scales well
- **Database**: Indexed queries, connection pooling
- **Rate Limiting**: Prevents overload, 30 req/min per IP
- **Stateless API**: Horizontal scaling possible
- **WebSocket**: Requires sticky sessions for load balancing

### Bottlenecks
1. **Gemini API calls**: 1-3 seconds per request
   - Mitigation: Caching common queries
2. **Model loading**: 4.4GB FAISS index
   - Mitigation: Keep in memory, download once from S3
3. **Database connections**: Limited by RDS instance
   - Mitigation: Connection pooling, read replicas

---

## Security Considerations

### Authentication & Authorization
```
┌──────────────────────────────────────────────────────────────┐
│  Request → Rate Limiter → Auth Middleware → Route Handler   │
└──────────────────────────────────────────────────────────────┘
```

### Data Protection
- Passwords: N/A (email-based verification)
- Verification codes: In-memory, 10-minute expiry
- JWT tokens: HS256 signature, 30-minute expiry
- Database: SSL/TLS connections
- API: HTTPS only in production

### Input Validation
- Max string lengths enforced
- Type checking with Pydantic
- SQL injection prevention (SQLAlchemy ORM)
- XSS prevention (frontend sanitization)

### HIPAA Compliance Considerations (Future)
- Data encryption at rest
- Audit logging
- Access controls
- Data retention policies
- Patient consent management

---

## Monitoring and Logging

### Backend Logging
```python
print(f"🚀 Loading models...")
print(f"✅ Loaded {len(chunks)} patient cases")
print(f"📊 Case {case_id} created")
print(f"⚠️ Failed to send email: {error}")
```

### Error Handling
```
Try-Catch blocks →
  ↓
Log error details →
  ↓
Return structured error →
  ↓
{
  "error": "Failed to process request",
  "detail": "Database connection timeout",
  "status_code": 500
}
```

### Health Checks
```
GET / → {
  "status": "healthy",
  "database": "connected",
  "auth": "gmail_enabled",
  "stats": { ... }
}
```

---

This architecture document provides a comprehensive view of the MedRAG system's internal workings, data flows, and deployment structure. For implementation details, refer to the source code and PROJECT_OVERVIEW.md.
