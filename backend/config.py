"""
AEGIS-OS Configuration
Centralised settings management using environment variables.
"""
import os
from pathlib import Path
from typing import Optional

# ─── Base Paths ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATASET_DIR = BASE_DIR.parent / "dataset"

# ─── Application ─────────────────────────────────────────────────────────────
APP_NAME = "AEGIS-OS"
APP_VERSION = "3.0.0"
APP_ENV = os.getenv("APP_ENV", "development")
DEBUG = APP_ENV == "development"

# ─── Security / Auth ──────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "aegis-dev-secret-key-change-in-production-32chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# ─── Database — PostgreSQL ────────────────────────────────────────────────────
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "aegis_db")
POSTGRES_USER = os.getenv("POSTGRES_USER", "aegis_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "aegis_password")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
)

# ─── Database — Neo4j ────────────────────────────────────────────────────────
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j_password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# ─── AI / LLM ─────────────────────────────────────────────────────────────────
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

# Default LLM provider — auto-detected from available keys
def get_default_llm_provider() -> str:
    if ANTHROPIC_API_KEY:
        return "anthropic"
    if OPENAI_API_KEY:
        return "openai"
    if GEMINI_API_KEY:
        return "gemini"
    return "mock"  # graceful fallback for development

LLM_PROVIDER = os.getenv("LLM_PROVIDER", get_default_llm_provider())
LLM_MODEL = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")

# ─── OCR ─────────────────────────────────────────────────────────────────────
OCR_ENGINE = os.getenv("OCR_ENGINE", "tesseract")  # tesseract | google_vision | aws_textract
GOOGLE_VISION_API_KEY: Optional[str] = os.getenv("GOOGLE_VISION_API_KEY")

# ─── File Storage ─────────────────────────────────────────────────────────────
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")  # local | s3 | minio
STORAGE_LOCAL_PATH = os.getenv("STORAGE_LOCAL_PATH", str(BASE_DIR / "evidence_storage"))
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "aegis-evidence")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")

# ─── ChromaDB (Vector Store) ──────────────────────────────────────────────────
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "chroma_data"))

# ─── CORS ─────────────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

# ─── Lemma SDK ────────────────────────────────────────────────────────────────
LEMMA_API_KEY: Optional[str] = os.getenv("LEMMA_API_KEY")
LEMMA_WORKSPACE_ID: Optional[str] = os.getenv("LEMMA_WORKSPACE_ID")
LEMMA_MODE = os.getenv("LEMMA_MODE", "self-hosted")  # self-hosted | cloud

# ─── Encryption ───────────────────────────────────────────────────────────────
EVIDENCE_ENCRYPTION_KEY = os.getenv(
    "EVIDENCE_ENCRYPTION_KEY",
    "aegis-evidence-enc-key-32byteslong!"
)

# Ensure local storage dir exists
if STORAGE_BACKEND == "local":
    Path(STORAGE_LOCAL_PATH).mkdir(parents=True, exist_ok=True)
