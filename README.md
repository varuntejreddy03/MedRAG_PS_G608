# MedRAG - Medical Diagnosis Assistant

AI-powered medical diagnosis system using Retrieval-Augmented Generation (RAG) with clinical case database.

## 📚 Documentation

- **[📖 Project Overview](PROJECT_OVERVIEW.md)** - Comprehensive guide to the project, features, and components
- **[🏗️ Architecture & Flow](ARCHITECTURE_FLOW.md)** - Detailed system architecture with visual flow diagrams
- **[🚀 Deployment Guide](backend/deploy_guide.md)** - AWS deployment instructions
- **[🧪 API Documentation](API_DOCUMENTATION.md)** - Complete API reference (see below)

## Architecture

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python, FAISS vector search
- **Database**: PostgreSQL (AWS RDS)
- **Storage**: AWS S3 (model files)
- **AI**: Google Gemini 2.0, Sentence Transformers

## Features

- Clinical wizard for patient case submission
- Real-time AI diagnosis with medical reasoning
- Interactive chat interface
- Dashboard with analytics
- Email notifications
- Session management (30-min timeout)

## Setup

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download models from S3
python -c "from s3_loader import download_from_s3; download_from_s3()"

# Run
uvicorn main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

### Backend (.env)
```
DATABASE_URL=postgresql://...
S3_BUCKET_NAME=medrag-data-bucket
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
GEMINI_API_KEY=your-key
GMAIL_USER=your-email
GMAIL_APP_PASSWORD=your-password
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Deployment

See `backend/deploy_guide.md` for AWS EC2 deployment instructions.

## Model Files

Large model files (4.4GB FAISS index) are stored in S3 and downloaded on startup.

## Quick Start Guide

### For First-Time Users
1. Read the [Project Overview](PROJECT_OVERVIEW.md) to understand MedRAG
2. Check the [Architecture & Flow](ARCHITECTURE_FLOW.md) to see how it works
3. Follow the setup instructions above
4. For production deployment, see the [Deployment Guide](backend/deploy_guide.md)

### Project Structure
```
MedRAG_PS_G608/
├── backend/                 # FastAPI backend
│   ├── main.py              # Main API server
│   ├── database.py          # Database models and operations
│   ├── auth.py              # Authentication and email
│   ├── s3_loader.py         # S3 model file loader
│   ├── requirements.txt     # Python dependencies
│   └── models/              # AI models (downloaded from S3)
│
├── frontend/                # Next.js frontend
│   ├── app/                 # Next.js app directory
│   ├── components/          # React components
│   │   ├── clinical-wizard.tsx
│   │   ├── dashboard.tsx
│   │   ├── chat-interface.tsx
│   │   └── ...
│   └── package.json         # Node dependencies
│
├── PROJECT_OVERVIEW.md      # Comprehensive project documentation
├── ARCHITECTURE_FLOW.md     # System architecture and flows
└── README.md                # This file
```

## Contributing

Contributions are welcome! Please follow these steps:
1. Read the [Project Overview](PROJECT_OVERVIEW.md) to understand the codebase
2. Review the [Architecture & Flow](ARCHITECTURE_FLOW.md) to understand the system
3. Make your changes following the existing code style
4. Test your changes thoroughly
5. Submit a pull request with a clear description

## License

This project is for educational and research purposes. Consult with legal counsel before deploying in a clinical setting.

## Disclaimer

⚠️ **Medical Disclaimer**: This is a diagnostic **assistance** tool, not a replacement for professional medical advice. All diagnoses should be reviewed by qualified healthcare professionals.
