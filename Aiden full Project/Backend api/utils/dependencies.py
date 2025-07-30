# ===== DEPENDENCY INJECTION =====
# utils/dependencies.py
from database.db_manager import DatabaseManager
from scrapers.scraper import ScraperManager
from functools import lru_cache

@lru_cache()
def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    return DatabaseManager()

@lru_cache()
def get_scraper_manager() -> ScraperManager:
    """Get scraper manager instance"""
    return ScraperManager()
