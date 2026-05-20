"""
RAG Chain Module
Orchestrates the Retrieval-Augmented Generation pipeline
"""
from typing import List, Dict, Optional
from src.embeddings import EmbeddingGenerator
from src.vector_store import VectorStore
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGChain:
    """
    Retrieval-Augmented Generation pipeline
    Retrieves relevant context and generates responses
    """
    
    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG chain
        
        Args:
            embedding_model_name: Name of the embedding model to use
        """
        self.embedding_generator = EmbeddingGenerator(embedding_model_name)
        self.vector_store = VectorStore(
            embedding_dim=self.embedding_generator.get_embedding_dimension()
        )
        
    def index_document(self, chunks: List[Dict]):
        """
        Index document chunks into vector store
        
        Args:
            chunks: List of chunk dictionaries with 'text' field
        """
        if not chunks:
            logger.warning("No chunks provided for indexing")
            return
        
        # Extract texts
        texts = [chunk['text'] for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.embedding_generator.encode(texts)
        
        # Add to vector store
        self.vector_store.add_chunks(chunks, embeddings)
        logger.info(f"Indexed {len(chunks)} chunks")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant chunks for a query
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            
        Returns:
            List of retrieved chunks with scores
        """
        # Generate query embedding
        query_embedding = self.embedding_generator.encode_query(query)
        
        # Search vector store
        results = self.vector_store.search(query_embedding, top_k)
        
        logger.info(f"Retrieved {len(results)} chunks for query: '{query[:50]}...'")
        return results
    
    def get_context(self, query: str, top_k: int = 5) -> str:
        """
        Get concatenated context from retrieved chunks
        
        Args:
            query: User query
            top_k: Number of chunks to retrieve
            
        Returns:
            Concatenated context string
        """
        results = self.retrieve(query, top_k)
        
        if not results:
            return "No relevant context found."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"[Source {i}] (Relevance: {result['score']:.3f})\n{result['text']}\n")
        
        return "\n".join(context_parts)
    
    def clear_index(self):
        """Clear the vector store"""
        self.vector_store.clear()
        logger.info("Index cleared")
    
    def save_index(self, path: str):
        """Save index to disk"""
        self.vector_store.save(path)
    
    def load_index(self, path: str):
        """Load index from disk"""
        self.vector_store.load(path)


# Mock LLM for generating responses (since we don't have API keys)
class MockLLM:
    """Mock LLM for demonstration purposes"""
    
    @staticmethod
    def generate_response(query: str, context: str) -> str:
        """
        Generate a response based on query and context
        
        In production, replace with actual LLM API call
        """
        response = f"""
## AI Resume Analysis Report

### Query: {query}

### Analysis Based on Your Resume:

{context[:1000] if context else "No context available. Please upload a resume first."}

### Key Recommendations:

1. **Skills Assessment**: Based on your resume, here are key observations:
   - Your experience shows strong potential in the relevant areas
   - Consider adding more quantifiable achievements
   - Highlight technical skills more prominently

2. **Improvement Suggestions**:
   - Add specific metrics and numbers to your experience points
   - Include relevant keywords from the job description
   - Restructure bullet points for better readability

3. **ATS Optimization Tips**:
   - Use standard section headings (Experience, Education, Skills)
   - Include both hard and soft skills
   - Avoid complex formatting and graphics

### Next Steps:
- Review the job description thoroughly
- Customize your resume for each application
- Keep your resume to 1-2 pages maximum

*Note: This is a simulated response. For production, integrate with OpenAI/Gemini API.*
"""
        return response


# Test the module
if __name__ == "__main__":
    rag = RAGChain()
    print("RAG Chain initialized successfully")