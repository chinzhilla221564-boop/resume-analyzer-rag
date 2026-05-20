"""
Resume Analyzer Module
Core analysis logic using RAG
"""
from typing import Dict, List, Optional, Tuple
from src.pdf_processor import PDFProcessor
from src.text_chunker import TextChunker
from src.rag_chain import RAGChain, MockLLM
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResumeAnalyzer:
    """
    Resume Analyzer using RAG pipeline
    Analyzes resumes and provides improvement suggestions
    """
    
    def __init__(self):
        """Initialize the resume analyzer"""
        self.pdf_processor = PDFProcessor()
        self.text_chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
        self.rag_chain = RAGChain()
        self.llm = MockLLM()  # Use mock LLM, replace with real API if available
        self.current_resume_path = None
        self.current_resume_text = None
        
    def load_resume(self, file_path: str) -> bool:
        """
        Load and process a resume file
        
        Args:
            file_path: Path to the resume file
            
        Returns:
            True if successful, False otherwise
        """
        # Extract text
        text = self.pdf_processor.extract_text(file_path)
        
        if not text:
            logger.error("Failed to extract text from resume")
            return False
        
        self.current_resume_text = text
        self.current_resume_path = file_path
        
        # Chunk the text
        chunks = self.text_chunker.chunk_smart(text)
        
        # Index in vector store
        self.rag_chain.index_document(chunks)
        
        logger.info(f"Loaded and indexed resume: {file_path}")
        return True
    
    def analyze_against_job(self, job_description: str) -> Dict:
        """
        Analyze resume against a job description
        
        Args:
            job_description: Job description text
            
        Returns:
            Dictionary with analysis results
        """
        if not self.current_resume_text:
            return {"error": "No resume loaded. Please upload a resume first."}
        
        # Retrieve relevant resume sections for the job
        relevant_chunks = self.rag_chain.retrieve(job_description, top_k=5)
        
        # Build context from retrieved chunks
        context = "\n\n".join([chunk['text'] for chunk in relevant_chunks])
        
        # Generate analysis prompt
        analysis_prompt = self._build_analysis_prompt(
            job_description, context, relevant_chunks
        )
        
        # Get LLM response
        analysis = self.llm.generate_response(
            query="Analyze my resume against this job description",
            context=analysis_prompt
        )
        
        # Calculate match score
        match_score = self._calculate_match_score(relevant_chunks)
        
        # Extract missing keywords
        missing_keywords = self._extract_missing_keywords(
            job_description, context
        )
        
        return {
            "analysis": analysis,
            "match_score": match_score,
            "missing_keywords": missing_keywords,
            "relevant_chunks": [
                {"text": chunk['text'][:200] + "...", "score": chunk['score']}
                for chunk in relevant_chunks
            ]
        }
    
    def _build_analysis_prompt(self, job_desc: str, context: str, chunks: List) -> str:
        """Build prompt for resume analysis"""
        prompt = f"""
JOB DESCRIPTION:
{job_desc}

RELEVANT RESUME SECTIONS:
{context}

RETRIEVAL RELEVANCE SCORES:
{[f"Section {i+1}: {c['score']:.3f}" for i, c in enumerate(chunks)]}

Please provide:
1. How well the resume matches the job description
2. Missing skills or keywords
3. Specific improvements for the resume
4. ATS optimization suggestions
5. Potential interview questions based on gaps
"""
        return prompt
    
    def _calculate_match_score(self, relevant_chunks: List) -> float:
        """
        Calculate match score based on retrieval relevance
        
        Returns:
            Score between 0 and 100
        """
        if not relevant_chunks:
            return 0.0
        
        # Average similarity score (cosine similarity is between -1 and 1)
        # Normalize to 0-100 range
        avg_score = sum(c['score'] for c in relevant_chunks) / len(relevant_chunks)
        
        # Convert from cosine similarity range to percentage
        # Cosine similarity of 0.5 becomes 75%, 0.8 becomes 90%
        normalized_score = (avg_score + 1) / 2 * 100
        
        return round(min(100, max(0, normalized_score)), 2)
    
    def _extract_missing_keywords(self, job_desc: str, context: str) -> List[str]:
        """
        Extract keywords from job description not found in resume
        
        This is a simple implementation. For production, use NLP techniques.
        """
        # Common tech keywords to check
        common_keywords = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue',
            'machine learning', 'ai', 'data science', 'sql', 'nosql',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'git',
            'agile', 'scrum', 'leadership', 'communication', 'teamwork',
            'project management', 'critical thinking', 'problem solving'
        ]
        
        job_lower = job_desc.lower()
        context_lower = context.lower()
        
        missing = []
        for keyword in common_keywords:
            if keyword in job_lower and keyword not in context_lower:
                missing.append(keyword)
        
        return missing[:10]  # Return top 10 missing keywords
    
    def generate_improvement_suggestions(self) -> str:
        """
        Generate general improvement suggestions for the resume
        
        Returns:
            Improvement suggestions text
        """
        if not self.current_resume_text:
            return "No resume loaded. Please upload a resume first."
        
        # Get overall resume structure and content
        chunks = self.rag_chain.retrieve("resume structure and content", top_k=3)
        context = "\n".join([c['text'] for c in chunks])
        
        suggestions = self.llm.generate_response(
            query="Suggest improvements for my resume",
            context=f"Current resume sections:\n{context}"
        )
        
        return suggestions
    
    def clear_resume(self):
        """Clear current resume from memory"""
        self.rag_chain.clear_index()
        self.current_resume_path = None
        self.current_resume_text = None
        logger.info("Cleared resume from memory")


# Test the module
if __name__ == "__main__":
    analyzer = ResumeAnalyzer()
    print("Resume Analyzer initialized successfully")