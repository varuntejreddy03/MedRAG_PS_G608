"""Knowledge Graph service for medical relationships."""

import os
import networkx as nx
from typing import List, Dict

class KnowledgeGraph:
    """Medical knowledge graph for disease-symptom relationships."""
    
    def __init__(self):
        self.graph = None
        self.graph_path = "models/knowledge_graph.graphml.xml"
        self._load_graph()
    
    def _load_graph(self):
        """Load knowledge graph from file."""
        try:
            if os.path.exists(self.graph_path):
                self.graph = nx.read_graphml(self.graph_path)
                print(f"✅ Loaded knowledge graph with {self.graph.number_of_nodes()} nodes")
            else:
                print("⚠️ Knowledge graph file not found, creating empty graph")
                self.graph = nx.DiGraph()
        except Exception as e:
            print(f"Knowledge graph loading failed: {e}")
            self.graph = nx.DiGraph()
    
    def get_related_symptoms(self, disease: str, max_results: int = 5) -> List[str]:
        """Get symptoms related to a disease."""
        if not self.graph or disease not in self.graph:
            return []
        
        try:
            neighbors = list(self.graph.neighbors(disease))
            return neighbors[:max_results]
        except Exception as e:
            print(f"Error getting related symptoms: {e}")
            return []
    
    def get_related_diseases(self, symptom: str, max_results: int = 5) -> List[str]:
        """Get diseases related to a symptom."""
        if not self.graph or symptom not in self.graph:
            return []
        
        try:
            # Get predecessors (diseases that have this symptom)
            predecessors = list(self.graph.predecessors(symptom))
            return predecessors[:max_results]
        except Exception as e:
            print(f"Error getting related diseases: {e}")
            return []
    
    def get_disease_info(self, disease: str) -> Dict:
        """Get detailed information about a disease."""
        if not self.graph or disease not in self.graph:
            return {}
        
        try:
            node_data = self.graph.nodes[disease]
            symptoms = self.get_related_symptoms(disease)
            
            return {
                "disease": disease,
                "symptoms": symptoms,
                "attributes": dict(node_data),
                "connections": self.graph.degree(disease)
            }
        except Exception as e:
            print(f"Error getting disease info: {e}")
            return {}
    
    def find_path(self, source: str, target: str) -> List[str]:
        """Find shortest path between two nodes."""
        if not self.graph or source not in self.graph or target not in self.graph:
            return []
        
        try:
            path = nx.shortest_path(self.graph, source, target)
            return path
        except nx.NetworkXNoPath:
            return []
        except Exception as e:
            print(f"Error finding path: {e}")
            return []
    
    def get_graph_stats(self) -> Dict:
        """Get statistics about the knowledge graph."""
        if not self.graph:
            return {}
        
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "density": nx.density(self.graph),
            "is_directed": self.graph.is_directed()
        }

knowledge_graph = KnowledgeGraph()
