"""FastAPI application initialization with middleware and routing."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.database import engine, Base
from .api import auth_router, users_router, diagnosis_router, rag_router
from .api.chat import router as chat_router
from .api.knowledge import router as knowledge_router
from .core.config import settings

# Validate required environment variables
settings.validate_required_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="Medical Diagnosis Assistant using RAG",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://100.88.41.29:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(diagnosis_router)
app.include_router(rag_router)
app.include_router(chat_router)
app.include_router(knowledge_router)

@app.get("/")
async def root():
    """Root endpoint returning API status."""
    return {"message": "MedRAG API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "service": "MedRAG API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)