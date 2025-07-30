import os
from typing import Dict, Any

class Settings:
    """Application settings"""
    
    # Database
    DATABASE_PATH: str = os.getenv('DATABASE_PATH', 'permits.db')
    
    # API Settings
    API_TITLE: str = "Multi-City Permits Dashboard"
    API_VERSION: str = "2.0.0"
    API_HOST: str = os.getenv('API_HOST', '0.0.0.0')
    API_PORT: int = int(os.getenv('API_PORT', '8000'))
    
    # Scraping Settings
    DEFAULT_SCRAPE_HOUR: int = int(os.getenv('DEFAULT_SCRAPE_HOUR', '6'))
    DEFAULT_SCRAPE_MINUTE: int = int(os.getenv('DEFAULT_SCRAPE_MINUTE', '0'))
    MAX_RECORDS_PER_SCRAPE: int = int(os.getenv('MAX_RECORDS_PER_SCRAPE', '10000'))
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
    RATE_LIMIT_WINDOW: int = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))
    
    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR: str = os.getenv('LOG_DIR', 'logs')

settings = Settings()

