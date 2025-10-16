# ===== DEPENDENCY INJECTION =====
# utils/dependencies.py
from app_final.database.db_manager import DatabaseManager
from app_final.scrapers.scraper import ScraperManager
from functools import lru_cache

@lru_cache()
def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    return DatabaseManager()

@lru_cache()
def get_scraper_manager() -> ScraperManager:
    """Get scraper manager instance"""
    return ScraperManager()
