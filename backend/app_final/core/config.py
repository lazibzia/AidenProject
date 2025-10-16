import os
from typing import Optional

# Database configuration
PERMITS_DB_PATH = 'permits.db'
CLIENTS_DB_PATH = 'permits.db'

# Email configuration
GMAIL_USER = 'rajalazibzia32@gmail.com'
GMAIL_PASSWORD = 'mxar qjrh dobm stfq'  # REMOVE BEFORE COMMITTING TO GIT

# RAG configuration
RAG_INDEX_DIR = "rag_index"

# Environment variables (override with .env file)
def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable with fallback to default"""
    return os.getenv(key, default)

# Database paths (can be overridden by environment)
PERMITS_DB_PATH = get_env_var('PERMITS_DB_PATH', PERMITS_DB_PATH)
CLIENTS_DB_PATH = get_env_var('CLIENTS_DB_PATH', CLIENTS_DB_PATH)

# Email settings (can be overridden by environment)
GMAIL_USER = get_env_var('GMAIL_USER', GMAIL_USER)
GMAIL_PASSWORD = get_env_var('GMAIL_PASSWORD', GMAIL_PASSWORD)

# RAG settings
RAG_INDEX_DIR = get_env_var('RAG_INDEX_DIR', RAG_INDEX_DIR)