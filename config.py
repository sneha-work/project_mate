# config.py - Environment & Application Configuration
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load .env file if it exists
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Ollama Cloud Configuration
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "https://api.ollama.com")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.3:70b")

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

# App Security
SECRET_KEY = os.getenv("SECRET_KEY", "researchmate-super-secret-key-academic-ai-2026")

# Storage Directories
UPLOADS_DIR = BASE_DIR / "uploads"
EXPORTS_DIR = BASE_DIR / "exports"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "0.0.0.0")
