"""
Configuration file for Resume Analyzer RAG System
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
VECTOR_STORE_DIR = BASE_DIR / "vector_store"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
VECTOR_STORE_DIR.mkdir(exist_ok=True)

# Model configurations
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Lightweight embedding model
CHUNK_SIZE = 1000  # Text chunk size in characters
CHUNK_OVERLAP = 200  # Overlap between chunks

# RAG Configuration
TOP_K_RESULTS = 5  # Number of relevant chunks to retrieve

# Streamlit settings
STREAMLIT_TITLE = "AI Resume Analyzer - RAG System"
STREAMLIT_ICON = "📄"

# File upload settings
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = [".pdf", ".txt"]

# API Keys (set as environment variables)
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# For free tier, we'll use local embeddings and a mock LLM
# To use real LLM, uncomment and set your API key
USE_LOCAL_LLM = True  # Set to False if using API-based LLM