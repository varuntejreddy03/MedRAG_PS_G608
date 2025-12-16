"""RAG Engine for medical diagnosis using Gemini AI and FAISS vector search."""

import os
from google import genai
from sentence_transformers import SentenceTransformer
import numpy as np
from .faiss_loader import faiss_loader
from ..core.config import settings

class RAGEngine:
    """Retrieval-Augmented Generation engine for medical diagnosis."""
    
    def __init__(self):
        """Initialize RAG engine with Gemini AI and sentence transformer."""
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        os.environ['GEMINI_API_KEY'] = settings.gemini_api_key
        self.client = genai.Client()
        self.encoder = None
        self._load_encoder()
    
    def _load_encoder(self):
        """Load sentence transformer model for text encoding."""
        try:
            self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception as e:
            print(f"Encoder loading failed: {e}")
    
    def generate_diagnosis(self, symptoms: str, age: int, gender: str, medical_history: str = "") -> dict:
        """Generate medical diagnosis using RAG approach.
        
        Args:
            symptoms: Patient symptoms description
            age: Patient age
            gender: Patient gender
            medical_history: Patient medical history
            
        Returns:
            Dictionary containing diagnosis, confidence, and similar cases count
        """
        if not self.encoder:
            return self._fallback_response()
            
        try:
            # Encode query
            query_text = f"Patient: {age} year old {gender}. Symptoms: {symptoms}. History: {medical_history}"
            query_vector = self.encoder.encode([query_text]).astype('float32')
            
            # Search similar cases using FAISS
            print(f"🔍 FAISS: Searching for similar cases...")
            similar_cases = faiss_loader.search(query_vector, k=5)
            print(f"✅ FAISS: Found {len(similar_cases)} similar cases")
            
            if similar_cases:
                print(f"📊 FAISS: Top similarity score: {similar_cases[0]['score']:.4f}")
                for i, case in enumerate(similar_cases[:3]):
                    print(f"   Case {i+1}: Score={case['score']:.4f}, Text={case['text'][:100]}...")
            
            # Build context from FAISS results
            context = "\n\n".join([f"Case {i+1} (Similarity: {case['score']:.2f}):\n{case['text']}" 
                                    for i, case in enumerate(similar_cases)])
            
            # Generate diagnosis using Gemini with FAISS context
            prompt = f"""
You are a medical AI assistant. Based on similar cases from our medical database and patient information, provide a differential diagnosis.

=== SIMILAR CASES FROM DATABASE (Retrieved via FAISS) ===
{context}

=== CURRENT PATIENT ===
Age: {age}
Gender: {gender}
Symptoms: {symptoms}
Medical History: {medical_history}

Provide a structured diagnosis with:
1. Primary Diagnosis
2. Differential Diagnoses (top 3 alternatives)
3. Recommended Tests (5-7 tests)
4. Treatment Recommendations
5. Confidence Level (High/Medium/Low)

Format your response as clean text with clear sections.
"""
            
            # Use gemini-2.5-flash-lite (10 RPM, 250K TPM)
            response = self.client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt
            )
            
            return {
                "diagnosis": response.text,
                "similar_cases": len(similar_cases),
                "confidence": "Medium",
                "faiss_retrieval": {
                    "cases_found": len(similar_cases),
                    "top_similarity": similar_cases[0]["score"] if similar_cases else 0
                },
                "model_used": settings.gemini_model
            }
            
        except Exception as e:
            print(f"RAG generation failed: {e}")
            return self._fallback_response()
    
    def chat_response(self, message: str, context: str = "") -> str:
        """Generate chat response for medical queries.
        
        Args:
            message: User message/question
            context: Additional context for the response
            
        Returns:
            AI-generated response string
        """
        try:
            prompt = f"""
            You are a medical AI assistant. Answer the following question based on medical knowledge.
            
            Context: {context}
            Question: {message}
            
            Provide a helpful, accurate response. Always recommend consulting healthcare professionals for serious concerns.
            """
            
            response = self.client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=prompt
            )
            return response.text
            
        except Exception as e:
            print(f"Chat response failed: {e}")
            return "I'm sorry, I couldn't process your request. Please try again."
    
    def _fallback_response(self) -> dict:
        """Return fallback response when diagnosis generation fails."""
        return {
            "diagnosis": "Unable to generate diagnosis. Please consult a medical professional.",
            "similar_cases": 0,
            "confidence": "Low"
        }

rag_engine = RAGEngine()