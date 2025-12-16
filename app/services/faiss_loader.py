import faiss
import json
import os
from .s3_service import s3_service

class FAISSLoader:
    def __init__(self):
        self.index = None
        self.chunks = None
        self.model_dir = "models"
        self.index_path = os.path.join(self.model_dir, "chunked_ehr_index.faiss")
        self.chunks_path = os.path.join(self.model_dir, "patient_chunks.json")
    
    def download_models_from_s3(self) -> bool:
        try:
            # Download FAISS index
            if not os.path.exists(self.index_path):
                success = s3_service.download_file("models/chunked_ehr_index.faiss", self.index_path)
                if not success:
                    return False
            
            # Download chunks
            if not os.path.exists(self.chunks_path):
                success = s3_service.download_file("models/patient_chunks.json", self.chunks_path)
                if not success:
                    return False
            
            return True
        except Exception as e:
            print(f"Model download failed: {e}")
            return False
    
    def load_index(self) -> bool:
        try:
            if not os.path.exists(self.index_path):
                if not self.download_models_from_s3():
                    return False
            
            self.index = faiss.read_index(self.index_path)
            
            with open(self.chunks_path, 'r') as f:
                self.chunks = json.load(f)
            
            return True
        except Exception as e:
            print(f"FAISS loading failed: {e}")
            return False
    
    def search(self, query_vector, k=5):
        if self.index is None or self.chunks is None:
            if not self.load_index():
                return []
        
        try:
            distances, indices = self.index.search(query_vector, k)
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.chunks):
                    chunk = self.chunks[idx]
                    text = chunk if isinstance(chunk, str) else chunk.get("text", str(chunk))
                    results.append({
                        "text": text,
                        "score": float(distances[0][i])
                    })
            return results
        except Exception as e:
            print(f"FAISS search failed: {e}")
            return []

faiss_loader = FAISSLoader()