# MedRAG API Documentation

Complete API reference for the MedRAG Medical Diagnosis Assistant.

**Base URL**: `http://localhost:8000` (development) or `https://your-domain.com` (production)

## Table of Contents
1. [Authentication](#authentication)
2. [Diagnosis](#diagnosis)
3. [Case Management](#case-management)
4. [Chat](#chat)
5. [Dashboard](#dashboard)
6. [Email](#email)
7. [Error Responses](#error-responses)

---

## Authentication

### Send Verification Code

Send a 6-digit verification code to the user's email.

**Endpoint**: `POST /send-verification`

**Alternative**: `POST /auth/send-code`

**Request Body**:
```json
{
  "email": "user@example.com"
}
```

**Response**: `200 OK`
```json
{
  "message": "Verification code sent",
  "success": true
}
```

**Errors**:
- `500 Internal Server Error` - Failed to send email

---

### Verify Code and Login

Verify the code and receive a JWT token.

**Endpoint**: `POST /verify-code`

**Alternative**: `POST /auth/verify`

**Request Body**:
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**Response**: `200 OK`
```json
{
  "message": "Authentication successful",
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "email": "user@example.com",
    "name": "User"
  }
}
```

**Errors**:
- `400 Bad Request` - Invalid or expired code
- `422 Unprocessable Entity` - Invalid request format

**Notes**:
- Verification codes expire after 10 minutes
- Tokens expire after 30 minutes
- Include token in subsequent requests: `Authorization: Bearer <token>`

---

## Diagnosis

### Single Diagnosis Request

Get a diagnosis for a patient query using RAG.

**Endpoint**: `POST /diagnose`

**Authentication**: Required

**Request Body**:
```json
{
  "query": "45 year old male with chest pain and shortness of breath",
  "k": 5
}
```

**Parameters**:
- `query` (string, required): Patient symptoms and information (max 1000 characters)
- `k` (integer, optional): Number of similar cases to retrieve (default: 5)

**Response**: `200 OK`
```json
{
  "query": "45 year old male with chest pain and shortness of breath",
  "diagnosis": "Possible NSTEMI (Non-ST Elevation Myocardial Infarction)",
  "reasoning": "### Diagnoses\n1. Possible NSTEMI...\n\n### Follow-up Questions\n1. Is the chest pain radiating?...\n\n### Tests\n1. ECG...\n\n### Treatment\nImmediate: Aspirin...",
  "confidence": 85,
  "matches": [
    "45yo male, acute chest pain, elevated troponin → MI",
    "50yo male, chest pain, ECG changes → unstable angina",
    "42yo male, chest pain, sweating → acute MI"
  ],
  "differentials": ["Alternative diagnosis 1", "Alternative diagnosis 2"],
  "tests": ["ECG", "Blood work", "Chest X-ray"],
  "actions": ["Monitor vital signs", "Administer medication", "Consult specialist"],
  "questions": ["Any family history?", "Previous episodes?", "Current medications?"]
}
```

**Errors**:
- `401 Unauthorized` - Missing or invalid token
- `422 Unprocessable Entity` - Invalid request format
- `429 Too Many Requests` - Rate limit exceeded (30 requests/minute)

---

## Case Management

### Submit Case

Submit a complete patient case for diagnosis.

**Endpoint**: `POST /cases`

**Authentication**: Required

**Request Body**:
```json
{
  "patient": {
    "fullName": "John Doe",
    "age": 45,
    "gender": "Male",
    "phone": "+1234567890",
    "email": "john@example.com"
  },
  "manifestations": {
    "complaint": "Severe chest pain",
    "symptoms": ["Chest pain", "Shortness of breath", "Sweating"]
  },
  "history": {
    "files": [],
    "manualHistory": "Smoker for 20 years, family history of heart disease"
  }
}
```

**Parameters**:
- `patient.fullName` (string, required): Patient's full name
- `patient.age` (integer, required): Patient's age
- `patient.gender` (string, required): Patient's gender
- `patient.phone` (string, optional): Contact phone number
- `patient.email` (string, optional): Email for diagnosis report
- `manifestations.complaint` (string, required): Chief complaint
- `manifestations.symptoms` (array, optional): List of symptoms
- `history.manualHistory` (string, optional): Medical history
- `history.files` (array, optional): Uploaded file references

**Response**: `200 OK`
```json
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
      "50yo male, chest pain, ECG changes → unstable angina"
    ]
  }
}
```

**Errors**:
- `401 Unauthorized` - Missing or invalid token
- `422 Unprocessable Entity` - Invalid request format
- `500 Internal Server Error` - Database or processing error

**Notes**:
- If email is provided, a diagnosis report will be sent automatically
- Case ID format: `CASE-XXXXXXXX` (8 uppercase hex characters)

---

### List Cases

Get a paginated list of all cases.

**Endpoint**: `GET /cases`

**Authentication**: Required

**Query Parameters**:
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Results per page (default: 10, max: 100)

**Example**: `GET /cases?page=1&per_page=20`

**Response**: `200 OK`
```json
{
  "cases": [
    {
      "id": "CASE-A3F9B27E",
      "patient_id": 123,
      "full_name": "John Doe",
      "age": 45,
      "gender": "Male",
      "email": "john@example.com",
      "complaint": "Severe chest pain",
      "symptoms": ["Chest pain", "Shortness of breath", "Sweating"],
      "history": "Smoker for 20 years...",
      "diagnosis": "Possible NSTEMI",
      "confidence": 85.0,
      "status": "diagnosed",
      "reasoning": "### Diagnoses...",
      "matches": ["45yo male..."],
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

---

### Get Case by ID

Retrieve details of a specific case.

**Endpoint**: `GET /cases/{case_id}`

**Authentication**: Required

**Path Parameters**:
- `case_id` (string, required): The case ID (e.g., "CASE-A3F9B27E")

**Example**: `GET /cases/CASE-A3F9B27E`

**Response**: `200 OK`
```json
{
  "id": "CASE-A3F9B27E",
  "full_name": "John Doe",
  "age": 45,
  "gender": "Male",
  "email": "john@example.com",
  "complaint": "Severe chest pain",
  "symptoms": ["Chest pain", "Shortness of breath", "Sweating"],
  "diagnosis": "Possible NSTEMI",
  "confidence": 85.0,
  "status": "diagnosed"
}
```

**Errors**:
- `404 Not Found` - Case ID does not exist

---

### Regenerate Diagnosis

Regenerate the diagnosis for an existing case.

**Endpoint**: `POST /cases/{case_id}/regenerate`

**Authentication**: Required

**Path Parameters**:
- `case_id` (string, required): The case ID

**Example**: `POST /cases/CASE-A3F9B27E/regenerate`

**Response**: `200 OK`
```json
{
  "case_id": "CASE-A3F9B27E",
  "status": "regenerated",
  "diagnosis_result": {
    "diagnosis": "Unstable angina",
    "reasoning": "### Diagnoses...",
    "confidence": 85.0
  }
}
```

**Errors**:
- `404 Not Found` - Case ID does not exist

**Notes**:
- Re-runs the entire RAG diagnosis process
- Updates the case record with new diagnosis
- Previous diagnosis is overwritten

---

### Export Case

Export case data for external use.

**Endpoint**: `GET /export/{case_id}`

**Authentication**: Required

**Path Parameters**:
- `case_id` (string, required): The case ID

**Example**: `GET /export/CASE-A3F9B27E`

**Response**: `200 OK`
```json
{
  "case_id": "CASE-A3F9B27E",
  "export_data": {
    "id": "CASE-A3F9B27E",
    "full_name": "John Doe",
    "age": 45,
    "gender": "Male",
    "complaint": "Severe chest pain",
    "symptoms": ["Chest pain", "Shortness of breath"],
    "diagnosis": "Possible NSTEMI",
    "confidence": 85.0,
    "status": "diagnosed"
  },
  "exported_at": "2024-01-15T10:30:00Z"
}
```

**Errors**:
- `404 Not Found` - Case ID does not exist

---

## Chat

### Chat (REST API)

Send a chat message and get an AI response.

**Endpoint**: `POST /chat`

**Authentication**: Required

**Request Body**:
```json
{
  "message": "What could cause chest pain in a young adult?",
  "session_id": "session_abc123"
}
```

**Parameters**:
- `message` (string, required): User's message (max 500 characters)
- `session_id` (string, optional): Session ID for context (auto-generated if not provided)

**Response**: `200 OK`
```json
{
  "response": "Chest pain in young adults can be caused by several conditions including costochondritis (inflammation of chest wall cartilage), anxiety or panic attacks, gastroesophageal reflux (GERD), or in rare cases, early heart disease. Based on similar cases...",
  "session_id": "session_abc123",
  "matches": [
    "25yo male, chest pain, anxiety → panic disorder",
    "30yo female, chest pain, GERD → reflux esophagitis"
  ]
}
```

**Notes**:
- Responses are limited to 80 words (250 tokens)
- Chat history (last 3 messages) is used for context
- Session timeout: 30 minutes

---

### Chat (WebSocket)

Real-time bidirectional chat communication.

**Endpoint**: `WS /chat/{session_id}`

**Authentication**: Token should be passed in the connection handshake or first message

**Path Parameters**:
- `session_id` (string, required): Unique session identifier

**Example Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/chat/session_abc123');

// Send message
ws.send(JSON.stringify({
  query: "What could cause my symptoms?",
  k: 5
}));

// Receive response
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data.response);
  console.log(data.matches);
  console.log(data.session_id);
};
```

**Message Format (Client → Server)**:
```json
{
  "query": "What could cause my symptoms?",
  "k": 5
}
```

**Message Format (Server → Client)**:
```json
{
  "response": "Based on your symptoms...",
  "matches": [
    "Similar case 1",
    "Similar case 2",
    "Similar case 3"
  ],
  "session_id": "session_abc123"
}
```

**Notes**:
- Session is created automatically on connection
- Messages are stored in database for history
- Connection closes on client disconnect or 30-minute timeout

---

### Clear Chat History

Delete all messages in a chat session.

**Endpoint**: `DELETE /chat/{session_id}`

**Authentication**: Required

**Path Parameters**:
- `session_id` (string, required): The session ID

**Example**: `DELETE /chat/session_abc123`

**Response**: `200 OK`
```json
{
  "message": "Chat history cleared"
}
```

**Notes**:
- This actually resets the session (creates a new empty session with the same ID)
- Previous messages are replaced with an empty array

---

## Dashboard

### Health Check

Check API status and get basic statistics.

**Endpoint**: `GET /`

**Authentication**: Not required

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "message": "MedRAG API is running",
  "database": "connected",
  "auth": "gmail_enabled",
  "stats": {
    "total_cases": 150,
    "pending_cases": 5,
    "diagnosed_cases": 145,
    "recent_cases": 145
  }
}
```

---

### Get Dashboard Statistics

Get detailed statistics for the dashboard.

**Endpoint**: `GET /dashboard/stats`

**Authentication**: Required

**Response**: `200 OK`
```json
{
  "total_cases": 150,
  "pending_cases": 5,
  "diagnosed_cases": 145,
  "recent_cases": 145
}
```

---

## Email

### Send Patient Email

Send a diagnosis report email to a patient.

**Endpoint**: `POST /send-patient-email`

**Authentication**: Required

**Request Body**:
```json
{
  "email": "patient@example.com",
  "case_id": "CASE-A3F9B27E",
  "patient_name": "John Doe",
  "diagnosis": "Possible NSTEMI"
}
```

**Response**: `200 OK`
```json
{
  "message": "Email sent successfully",
  "success": true
}
```

**Errors**:
- `500 Internal Server Error` - Failed to send email

**Notes**:
- Email is sent via Gmail SMTP
- Subject: "MedRAG Diagnosis Report - Case {case_id}"
- Body includes case ID and diagnosis summary

---

### Submit Feedback

Submit user feedback (feature not fully implemented).

**Endpoint**: `POST /feedback`

**Authentication**: Required

**Request Body**:
```json
{
  "feedback": "The diagnosis was very helpful...",
  "rating": 5,
  "case_id": "CASE-A3F9B27E"
}
```

**Response**: `200 OK`
```json
{
  "message": "Feedback submitted successfully",
  "feedback_id": "FB-A1B2C3D4"
}
```

---

## Error Responses

### Standard Error Format

All errors follow this format:

```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "status_code": 400
}
```

### Common HTTP Status Codes

- `200 OK` - Request succeeded
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication token
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded (30 requests/minute per IP)
- `500 Internal Server Error` - Server error

### Rate Limiting

**Limit**: 30 requests per minute per IP address

**Response**: `429 Too Many Requests`
```json
{
  "error": "Rate limit exceeded. Try again later."
}
```

**Headers**:
- Implement rate limit headers in production:
  - `X-RateLimit-Limit: 30`
  - `X-RateLimit-Remaining: 0`
  - `X-RateLimit-Reset: 1642345678`

---

## Request Examples

### Using cURL

**Authentication**:
```bash
# Send verification code
curl -X POST http://localhost:8000/send-verification \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'

# Verify code and get token
curl -X POST http://localhost:8000/verify-code \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","code":"123456"}'
```

**Submit Case**:
```bash
curl -X POST http://localhost:8000/cases \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "patient": {
      "fullName": "John Doe",
      "age": 45,
      "gender": "Male",
      "email": "john@example.com"
    },
    "manifestations": {
      "complaint": "Chest pain",
      "symptoms": ["Chest pain", "Shortness of breath"]
    }
  }'
```

**Get Cases**:
```bash
curl -X GET "http://localhost:8000/cases?page=1&per_page=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Using JavaScript (Fetch)

```javascript
// Send verification code
const sendCode = async (email) => {
  const response = await fetch('http://localhost:8000/send-verification', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  return await response.json();
};

// Verify code and login
const verifyCode = async (email, code) => {
  const response = await fetch('http://localhost:8000/verify-code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code })
  });
  const data = await response.json();
  localStorage.setItem('authToken', data.token);
  return data;
};

// Submit case
const submitCase = async (caseData) => {
  const token = localStorage.getItem('authToken');
  const response = await fetch('http://localhost:8000/cases', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(caseData)
  });
  return await response.json();
};

// Get cases
const getCases = async (page = 1, perPage = 10) => {
  const token = localStorage.getItem('authToken');
  const response = await fetch(
    `http://localhost:8000/cases?page=${page}&per_page=${perPage}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );
  return await response.json();
};

// WebSocket chat
const connectChat = (sessionId) => {
  const ws = new WebSocket(`ws://localhost:8000/chat/${sessionId}`);
  
  ws.onopen = () => {
    console.log('Connected to chat');
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Response:', data.response);
    console.log('Matches:', data.matches);
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  ws.onclose = () => {
    console.log('Disconnected from chat');
  };
  
  return ws;
};

// Send chat message
const sendChatMessage = (ws, message) => {
  ws.send(JSON.stringify({
    query: message,
    k: 5
  }));
};
```

### Using Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

# Send verification code
def send_verification(email):
    response = requests.post(
        f"{BASE_URL}/send-verification",
        json={"email": email}
    )
    return response.json()

# Verify code and login
def verify_code(email, code):
    response = requests.post(
        f"{BASE_URL}/verify-code",
        json={"email": email, "code": code}
    )
    data = response.json()
    return data["token"]

# Submit case
def submit_case(token, case_data):
    response = requests.post(
        f"{BASE_URL}/cases",
        headers={"Authorization": f"Bearer {token}"},
        json=case_data
    )
    return response.json()

# Get cases
def get_cases(token, page=1, per_page=10):
    response = requests.get(
        f"{BASE_URL}/cases",
        headers={"Authorization": f"Bearer {token}"},
        params={"page": page, "per_page": per_page}
    )
    return response.json()

# Example usage
email = "user@example.com"
send_verification(email)
code = input("Enter verification code: ")
token = verify_code(email, code)

case_data = {
    "patient": {
        "fullName": "John Doe",
        "age": 45,
        "gender": "Male"
    },
    "manifestations": {
        "complaint": "Chest pain",
        "symptoms": ["Chest pain", "Shortness of breath"]
    }
}

result = submit_case(token, case_data)
print(f"Case ID: {result['case_id']}")
print(f"Diagnosis: {result['diagnosis_result']['diagnosis']}")
```

---

## API Versioning

Currently, the API is unversioned (v1 implicit). Future versions may be released as:
- `/api/v2/...`

Breaking changes will be communicated in advance.

---

## CORS Configuration

**Allowed Origins** (Production):
- `https://psmedrag.vercel.app`
- `https://*.vercel.app`
- `http://localhost:3000` (Development)

**Allowed Methods**: All (`*`)

**Allowed Headers**: All (`*`)

**Credentials**: Enabled

---

## Security Best Practices

### Token Management
1. Store tokens securely (httpOnly cookies or secure storage)
2. Refresh tokens before expiration
3. Clear tokens on logout
4. Never share tokens

### Request Security
1. Always use HTTPS in production
2. Validate SSL certificates
3. Sanitize user inputs
4. Follow rate limits

### Data Privacy
1. Don't log sensitive patient data
2. Use secure connections for database
3. Implement proper access controls
4. Follow HIPAA guidelines if applicable

---

## Testing the API

### Health Check Test
```bash
curl http://localhost:8000/
```

Expected: `{"status": "healthy", ...}`

### Full Authentication Flow Test
```bash
# 1. Send code
curl -X POST http://localhost:8000/send-verification \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# 2. Check email for code

# 3. Verify (replace 123456 with actual code)
curl -X POST http://localhost:8000/verify-code \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","code":"123456"}'

# 4. Use returned token for authenticated requests
```

---

## Support

For issues or questions:
1. Check the [Project Overview](PROJECT_OVERVIEW.md)
2. Review the [Architecture & Flow](ARCHITECTURE_FLOW.md)
3. Examine backend logs for error details
4. Contact the development team

---

**API Version**: 2.0  
**Last Updated**: 2024  
**Backend Framework**: FastAPI 0.68+  
**OpenAPI Spec**: Available at `/docs` (Swagger UI) and `/redoc` (ReDoc)
