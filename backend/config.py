import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Flask configuration
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
PORT = int(os.getenv("PORT", "5000"))
HOST = os.getenv("HOST", "0.0.0.0")

# Storage paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_STORAGE_PATH = os.path.join(BASE_DIR, "storage", "pdfs")
VECTOR_DB_PATH = os.path.join(BASE_DIR, "storage", "vectors")

# Create directories if they don't exist
os.makedirs(PDF_STORAGE_PATH, exist_ok=True)
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# HuggingFace embedding model
HF_EMBEDDING_MODEL = os.getenv("HF_EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# PDF processing configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))