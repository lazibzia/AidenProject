from database.db_manager import DatabaseManager
from scrapers.scraper import ScraperManager

def get_db_manager():
    return DatabaseManager()

def get_scraper_manager():
    return ScraperManager()