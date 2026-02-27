import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# ChromaDB
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

# SQLite
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./data/insurance_hub.db")

# Chunking
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# Intent categories
INTENT_TYPES = [
    "new_application",
    "underwriting_status",
    "policy_query",
    "general_info",
    "document_upload",
]

# Agent names
AGENT_NAMES = {
    "new_application": "Application Servicing Agent",
    "underwriting_status": "Underwriting Support Agent",
    "policy_query": "Policy Servicing Agent",
    "general_info": "Policy Information Agent",
    "document_upload": "Document Intelligence Agent",
}

# Sentiment thresholds
SENTIMENT_HIGH_THRESHOLD = 0.7
SENTIMENT_LOW_THRESHOLD = 0.4
