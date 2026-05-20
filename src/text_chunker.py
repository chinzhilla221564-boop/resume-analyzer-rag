"""
Text Chunking Module
Splits extracted text into manageable chunks for embedding
"""
from typing import List, Dict
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextChunker:
    """Split text into overlapping chunks for better retrieval"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the text chunker
        
        Args:
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Overlap between consecutive chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_by_paragraphs(self, text: str) -> List[str]:
        """
        Split text by paragraphs first, then by size
        
        Args:
            text: Input text to split
            
        Returns:
            List of text chunks
        """
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Add the last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks
    
    def chunk_with_overlap(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks based on character count
        
        Args:
            text: Input text to split
            
        Returns:
            List of overlapping text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            
            # Find a good break point (end of sentence or space)
            if end < text_length:
                # Try to break at a sentence end
                sentence_end = text.rfind('. ', start, end)
                if sentence_end != -1 and sentence_end > start:
                    end = sentence_end + 2
                else:
                    # Break at last space
                    last_space = text.rfind(' ', start, end)
                    if last_space != -1:
                        end = last_space + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start with overlap
            start = end - self.chunk_overlap
        
        logger.info(f"Created {len(chunks)} overlapping chunks")
        return chunks
    
    def chunk_smart(self, text: str) -> List[Dict]:
        """
        Smart chunking with metadata
        
        Args:
            text: Input text to split
            
        Returns:
            List of dictionaries with chunk text and metadata
        """
        # Clean the text
        text = re.sub(r'\n+', '\n', text)  # Normalize newlines
        text = re.sub(r' +', ' ', text)    # Normalize spaces
        
        # Try paragraph-based chunking first
        chunks = self.chunk_by_paragraphs(text)
        
        # If we have very few large chunks, try overlapping
        if len(chunks) < 3 and len(text) > self.chunk_size * 2:
            chunks = self.chunk_with_overlap(text)
        
        # Add metadata to chunks
        chunks_with_metadata = []
        for i, chunk in enumerate(chunks):
            chunks_with_metadata.append({
                'id': i,
                'text': chunk,
                'length': len(chunk),
                'position': i
            })
        
        logger.info(f"Created {len(chunks_with_metadata)} chunks with metadata")
        return chunks_with_metadata


# Test the module
if __name__ == "__main__":
    chunker = TextChunker()
    test_text = "This is a test. " * 500
    chunks = chunker.chunk_smart(test_text)
    print(f"Created {len(chunks)} chunks")