"""
Embedding Generation Module
Creates vector embeddings from text chunks using Sentence Transformers
"""
from typing import List, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for text using Sentence Transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding model
        
        Args:
            model_name: Name of the SentenceTransformer model
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        try:
            logger.info(f"Loading embedding model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def encode(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for text(s)
        
        Args:
            texts: Single text string or list of texts
            batch_size: Batch size for processing
            
        Returns:
            Numpy array of embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=False,
                normalize_embeddings=True  # Normalize for cosine similarity
            )
            logger.info(f"Generated {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a search query (same as encode but more explicit)
        
        Args:
            query: Search query string
            
        Returns:
            Query embedding
        """
        return self.encode(query)
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings"""
        return self.embedding_dim


# Test the module
if __name__ == "__main__":
    generator = EmbeddingGenerator()
    test_texts = ["This is a test sentence.", "Another test here."]
    embeddings = generator.encode(test_texts)
    print(f"Embedding shape: {embeddings.shape}")