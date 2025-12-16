# MedRAG - Medical Diagnosis Assistant: Project Overview

## 🎯 What is MedRAG?

MedRAG is an **AI-powered medical diagnosis system** that uses **Retrieval-Augmented Generation (RAG)** technology to provide clinical diagnostic assistance. It combines a large clinical case database with advanced AI to analyze patient symptoms and suggest potential diagnoses.

### Key Concept: RAG (Retrieval-Augmented Generation)
Instead of relying solely on an AI model's training, RAG:
1. **Retrieves** similar cases from a database of 17,000+ clinical records
2. **Augments** the AI prompt with this relevant context
3. **Generates** informed diagnoses based on real medical cases

## 🏗️ Architecture Components

### Technology Stack

#### Backend
- **Framework**: FastAPI (Python) - Fast, modern API framework
- **AI Model**: Google Gemini 2.0 Flash - For diagnosis generation
- **Vector Search**: FAISS - Fast similarity search in medical case database
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2) - Convert text to vectors
- **Database**: PostgreSQL (AWS RDS) - Store cases, patients, chat history
- **Storage**: AWS S3 - Store large model files (4.4GB FAISS index)
- **Authentication**: JWT + Email verification (Gmail SMTP)

#### Frontend
- **Framework**: Next.js 14 (React 19)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI + shadcn/ui
- **Animations**: Framer Motion
- **State Management**: React Hooks

### Data Components

1. **FAISS Index** (chunked_ehr_index.faiss - 4.4GB)
   - Vector embeddings of 17,000+ patient cases
   - Enables fast semantic search

2. **Patient Chunks** (patient_chunks.json)
   - Text descriptions of patient cases
   - Includes symptoms, history, diagnoses

3. **Evidence Dictionary** (release_evidences.json)
   - Maps medical evidence codes (E_1, E_2, etc.) to descriptions
   - Example: E_52 → "Chest pain", E_65 → "Shortness of breath"

## 🔄 System Flow

### 1. User Authentication Flow
```
User enters email → Backend sends verification code → 
User enters code → Backend validates → JWT token issued → 
Session created (30-min timeout)
```

### 2. Case Submission Flow
```
Frontend: Clinical Wizard
├─ Step 1: Patient Information (name, age, gender, contact)
├─ Step 2: Chief Complaint & Symptoms
└─ Step 3: Medical History (optional)
    ↓
Backend: Process Submission
├─ Create patient record in database
├─ Create case record with unique ID
├─ Convert symptoms to vector embedding
├─ Search FAISS index for similar cases
├─ Retrieve top 5 similar cases
└─ Send to Gemini AI with context
    ↓
Gemini AI generates:
├─ Primary diagnosis
├─ Clinical reasoning
├─ Follow-up questions
├─ Recommended tests
└─ Treatment plan
    ↓
Backend stores results
└─ Sends email to patient (if provided)
```

### 3. Interactive Chat Flow
```
User sends message in chat →
Backend retrieves chat history →
Embeds message and searches FAISS →
Retrieves similar cases →
Sends context + history to Gemini →
AI generates response (max 80 words) →
Stores in chat session →
Returns to user via WebSocket
```

### 4. Dashboard Flow
```
User logs in →
Dashboard loads statistics:
├─ Total cases submitted
├─ Pending diagnoses
├─ Completed diagnoses
└─ Recent activity
    ↓
User can:
├─ View all cases (paginated)
├─ Search/filter cases
├─ View case details
├─ Regenerate diagnoses
└─ Export case data
```

## 🚀 Key Features

### 1. Clinical Wizard
- Multi-step form for detailed patient case submission
- Input validation and error handling
- File upload support for medical records
- Symptom selection with predefined options

### 2. AI Diagnosis Engine
- **Vector Similarity Search**: Finds relevant cases using FAISS
- **Context-Aware**: Uses top 3-5 similar cases for diagnosis
- **Structured Output**: Organized diagnosis with reasoning
- **Confidence Scoring**: Provides reliability metrics

### 3. Interactive Chat
- Real-time WebSocket communication
- Context-aware responses using chat history
- Similar case retrieval for each query
- Session management with 30-minute timeout

### 4. Dashboard Analytics
- Real-time statistics and metrics
- Case management and tracking
- Search and filter capabilities
- Export functionality

### 5. Email Notifications
- Verification codes for authentication
- Diagnosis reports sent to patients
- Case updates and notifications

## 🔐 Security Features

### Rate Limiting
- 30 requests per minute per IP address
- Prevents API abuse and DDoS attacks

### Authentication
- Email-based verification with 6-digit codes
- JWT tokens for session management
- 10-minute code expiration
- 30-minute session timeout

### Trusted Hosts
- Whitelist of allowed domains
- Prevents DNS rebinding attacks

### CORS Protection
- Configured for specific origins
- Credentials support enabled

### Input Validation
- Pydantic models for request validation
- Maximum length constraints
- Type checking and sanitization

## 📊 Data Models

### Patient
```python
{
  id: integer (auto-increment)
  full_name: string
  age: integer
  gender: string
  phone: string (optional)
  email: string (optional)
  created_at: datetime
}
```

### Case
```python
{
  id: string (CASE-XXXXXXXX)
  patient_id: integer (FK)
  complaint: text
  symptoms: json array
  history: text (optional)
  diagnosis: text
  confidence: float (0-100)
  status: enum ['pending', 'diagnosed']
  reasoning: text (full AI response)
  matches: json array (similar cases)
  created_at: datetime
  updated_at: datetime
}
```

### Chat Session
```python
{
  id: string (session_XXXXXXXX)
  messages: json array [{
    user: string,
    assistant: string,
    timestamp: datetime
  }]
  created_at: datetime
  updated_at: datetime
}
```

## 📡 API Endpoints

### Authentication
- `POST /send-verification` - Send verification code
- `POST /verify-code` - Verify code and login
- `POST /auth/send-code` - Alternative auth endpoint
- `POST /auth/verify` - Alternative verify endpoint

### Diagnosis
- `POST /diagnose` - Single diagnosis request (REST)
- `POST /chat` - Chat-based diagnosis (REST)
- `WS /chat/{session_id}` - Real-time chat (WebSocket)

### Case Management
- `POST /cases` - Submit new case
- `GET /cases` - List all cases (paginated)
- `GET /cases/{case_id}` - Get specific case
- `POST /cases/{case_id}/regenerate` - Regenerate diagnosis
- `GET /export/{case_id}` - Export case data

### Dashboard
- `GET /` - Health check and stats
- `GET /dashboard/stats` - Dashboard statistics

### Communication
- `POST /send-patient-email` - Send email to patient
- `POST /feedback` - Submit feedback

### Chat
- `DELETE /chat/{session_id}` - Clear chat history

## 🎨 Frontend Components

### Main Views
1. **Landing/Login** (`landing-hero.tsx`)
   - Hero section with animations
   - Email authentication form
   - Session management

2. **Dashboard** (`dashboard.tsx`)
   - Statistics cards
   - Case list with filters
   - Quick actions

3. **Diagnostic Dashboard** (`diagnostic-dashboard.tsx`)
   - Detailed case view
   - Diagnosis results
   - Regeneration options

4. **Clinical Wizard** (`clinical-wizard.tsx`)
   - Multi-step form
   - Patient information
   - Symptom selection
   - History input

5. **Chat Interface** (`chat-interface.tsx`)
   - Real-time messaging
   - Chat history
   - Context-aware responses

## 🌐 Deployment Architecture

### Development Environment
```
Frontend (localhost:3000) ←→ Backend (localhost:8000)
```

### Production Environment
```
Frontend (Vercel)
    ↓
Backend (AWS EC2)
    ↓
├─ PostgreSQL (AWS RDS)
└─ S3 (Model Storage)
```

### Model Loading Process
1. Backend starts up
2. Checks for model files locally
3. If missing, downloads from S3 using `s3_loader.py`
4. Loads models into memory:
   - Sentence transformer (embedding)
   - FAISS index (vector search)
   - Patient chunks (case database)
   - Evidence dictionary (medical terms)

## 🔧 Environment Configuration

### Backend (.env)
```env
DATABASE_URL=postgresql://user:pass@host:5432/db
S3_BUCKET_NAME=medrag-data-bucket
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
GEMINI_API_KEY=your-gemini-key
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📈 Performance Considerations

### Vector Search Optimization
- FAISS uses efficient indexing for fast similarity search
- Embedding model kept in memory for quick encoding
- Top-k results (typically 3-5) reduce API load

### Database Optimization
- Indexed queries on case_id and patient_id
- Pagination for large result sets
- Connection pooling with SQLAlchemy

### Caching Strategy
- Session data cached in memory (rate limiting)
- Verification codes cached temporarily
- Model files loaded once at startup

### Scalability
- Stateless API design (except WebSocket)
- Horizontal scaling possible with load balancer
- Database can be replicated for read operations

## 🧪 Testing

### Backend Tests
Location: `backend/test_backend.py`
- API endpoint testing
- Database operations
- Authentication flows

### Frontend Testing
- Component tests (not yet implemented)
- E2E tests (not yet implemented)

## 📝 Development Workflow

### Setup Development Environment
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -c "from s3_loader import download_from_s3; download_from_s3()"
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Making Changes
1. Create feature branch
2. Make minimal changes
3. Test locally
4. Commit and push
5. Create pull request

## 🎓 Learning Resources

### Technologies Used
- **FastAPI**: https://fastapi.tiangolo.com/
- **FAISS**: https://github.com/facebookresearch/faiss
- **Sentence Transformers**: https://www.sbert.net/
- **Google Gemini**: https://ai.google.dev/docs
- **Next.js**: https://nextjs.org/docs
- **PostgreSQL**: https://www.postgresql.org/docs/

### Medical Informatics
- RAG in Healthcare
- Clinical Decision Support Systems
- Medical NLP and Information Retrieval

## 🚨 Important Notes

### Medical Disclaimer
This is a diagnostic **assistance** tool, not a replacement for professional medical advice. All diagnoses should be reviewed by qualified healthcare professionals.

### Data Privacy
- Patient data stored securely in PostgreSQL
- HIPAA compliance considerations needed for production
- Email communications should use encrypted channels

### Model Limitations
- Based on training data up to model's cutoff date
- May not include latest medical research
- Requires validation against current medical guidelines

## 🔮 Future Enhancements

### Planned Features
1. Multi-language support
2. Medical image analysis
3. Integration with EHR systems
4. Doctor collaboration tools
5. Detailed audit logs
6. Advanced analytics and reporting
7. Mobile application
8. Voice input for symptoms

### Technical Improvements
1. Add comprehensive test coverage
2. Implement caching layer (Redis)
3. Add monitoring and logging (Sentry, Datadog)
4. Implement CI/CD pipeline
5. Add API documentation (Swagger UI)
6. Optimize database queries
7. Add real-time collaboration features
8. Implement backup and disaster recovery

## 📞 Support and Contribution

### Getting Help
- Check documentation in `backend/deploy_guide.md`
- Review API responses for error details
- Check backend logs for debugging

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

### Code Style
- Backend: Follow PEP 8 Python style guide
- Frontend: Use TypeScript strict mode
- Comments: Document complex logic
- Commits: Use clear, descriptive messages

## 📄 License

This project is for educational and research purposes. Consult with legal counsel before deploying in a clinical setting.

---

**Version**: 2.0  
**Author**: Varun Tej  
**Last Updated**: 2024
