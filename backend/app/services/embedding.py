import numpy as np
from typing import List, Optional
import logging
from sentence_transformers import SentenceTransformer
import asyncio

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding service with sentence transformer model"""
        self.model = SentenceTransformer(model_name)
        
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for list of texts"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, 
                self.model.encode, 
                texts
            )
            
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

# Global embedding service instance
embedding_service = EmbeddingService()

async def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate embeddings for texts"""
    return await embedding_service.generate_embeddings(texts)