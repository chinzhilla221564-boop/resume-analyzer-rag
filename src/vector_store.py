"""
Vector Store Module using FAISS
Stores and retrieves document embeddings
"""
import faiss
import numpy as np
from typing import List, Dict, Tuple, Optional
import pickle
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store for document chunks"""
    
    def __init__(self, embedding_dim: int, persist_dir: Optional[str] = None):
        """
        Initialize the vector store
        
        Args:
            embedding_dim: Dimension of embeddings
            persist_dir: Directory to persist the index
        """
        self.embedding_dim = embedding_dim
        self.persist_dir = persist_dir
        self.index = None
        self.chunks = []  # Store original text chunks
        self.metadata = []  # Store chunk metadata
        
        self._initialize_index()
        
        if persist_dir and os.path.exists(persist_dir):
            self.load()
    
    def _initialize_index(self):
        """Initialize FAISS index"""
        # Use inner product (cosine similarity on normalized vectors)
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        logger.info(f"Initialized FAISS index with dimension {self.embedding_dim}")
    
    def add_chunks(self, chunks: List[Dict], embeddings: np.ndarray):
        """
        Add chunks and their embeddings to the store
        
        Args:
            chunks: List of chunk dictionaries with 'text' and metadata
            embeddings: Numpy array of embeddings
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks and embeddings must match")
        
        # Convert to float32 for FAISS
        embeddings = embeddings.astype('float32')
        
        # Add to index
        self.index.add(embeddings)
        
        # Store chunks and metadata
        for chunk in chunks:
            self.chunks.append(chunk.get('text', ''))
            self.metadata.append({
                'id': chunk.get('id', len(self.metadata)),
                'position': chunk.get('position', len(self.metadata)),
                'length': chunk.get('length', 0)
            })
        
        logger.info(f"Added {len(chunks)} chunks to vector store. Total: {self.index.ntotal}")
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """
        Search for similar chunks
        
        Args:
            query_embedding: Query embedding
            k: Number of results to return
            
        Returns:
            List of dictionaries with text and similarity score
        """
        if self.index.ntotal == 0:
            logger.warning("Vector store is empty")
            return []
        
        # Ensure correct shape and type
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)
        query_embedding = query_embedding.astype('float32')
        
        # Search
        scores, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        # Prepare results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and idx < len(self.chunks):
                results.append({
                    'text': self.chunks[idx],
                    'score': float(score),
                    'metadata': self.metadata[idx] if idx < len(self.metadata) else {}
                })
        
        logger.info(f"Found {len(results)} results for query")
        return results
    
    def save(self, path: str):
        """
        Save the vector store to disk
        
        Args:
            path: Directory path to save
        """
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, str(save_path / "index.faiss"))
        
        # Save chunks and metadata
        with open(save_path / "chunks.pkl", 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'metadata': self.metadata
            }, f)
        
        logger.info(f"Saved vector store to {save_path}")
    
    def load(self, path: Optional[str] = None):
        """
        Load the vector store from disk
        
        Args:
            path: Directory path to load from
        """
        load_path = path or self.persist_dir
        if not load_path:
            raise ValueError("No path provided for loading")
        
        load_path = Path(load_path)
        
        # Load FAISS index
        index_path = load_path / "index.faiss"
        if index_path.exists():
            self.index = faiss.read_index(str(index_path))
            logger.info(f"Loaded FAISS index from {index_path}")
        
        # Load chunks and metadata
        chunks_path = load_path / "chunks.pkl"
        if chunks_path.exists():
            with open(chunks_path, 'rb') as f:
                data = pickle.load(f)
                self.chunks = data['chunks']
                self.metadata = data['metadata']
            logger.info(f"Loaded {len(self.chunks)} chunks from {chunks_path}")
    
    def clear(self):
        """Clear the vector store"""
        self._initialize_index()
        self.chunks = []
        self.metadata = []
        logger.info("Cleared vector store")
    
    def get_size(self) -> int:
        """Get number of chunks in store"""
        return self.index.ntotal


# Test the module
if __name__ == "__main__":
    store = VectorStore(embedding_dim=384)  # all-MiniLM-L6-v2 dimension
    print(f"Vector store initialized. Size: {store.get_size()}")