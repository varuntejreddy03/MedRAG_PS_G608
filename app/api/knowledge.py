"""Knowledge Graph API endpoints."""

from fastapi import APIRouter
from ..services.knowledge_graph import knowledge_graph

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

@router.get("/stats")
async def get_graph_stats():
    """Get knowledge graph statistics."""
    return knowledge_graph.get_graph_stats()

@router.get("/disease/{disease_name}")
async def get_disease_info(disease_name: str):
    """Get information about a specific disease."""
    return knowledge_graph.get_disease_info(disease_name)

@router.get("/symptoms/{disease_name}")
async def get_disease_symptoms(disease_name: str):
    """Get symptoms for a disease."""
    symptoms = knowledge_graph.get_related_symptoms(disease_name)
    return {"disease": disease_name, "symptoms": symptoms}

@router.get("/diseases/{symptom}")
async def get_symptom_diseases(symptom: str):
    """Get diseases related to a symptom."""
    diseases = knowledge_graph.get_related_diseases(symptom)
    return {"symptom": symptom, "diseases": diseases}
