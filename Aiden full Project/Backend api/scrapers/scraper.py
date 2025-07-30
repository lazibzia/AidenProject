from typing import Dict, List, Any
from abc import ABC, abstractmethod
import importlib
from config.cities import CITY_CONFIGS

class BaseScraper(ABC):
    """Base class for all city scrapers"""
    
    @abstractmethod
    def scrape(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Scrape permits for the date range"""
        pass
    
    @abstractmethod
    def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean scraped data"""
        pass

class ScraperManager:
    def __init__(self):
        self.scrapers = {}
        self._load_scrapers()
    
    def _load_scrapers(self):
        """Dynamically load scrapers for each city"""
        for city_name, config in CITY_CONFIGS.items():
            try:
                # Import the scraper module
                module_name = f"scrapers.{city_name.lower()}_scraper"
                module = importlib.import_module(module_name)
                
                # Get the scraper class
                scraper_class = getattr(module, config['scraper_class'])
                self.scrapers[city_name] = scraper_class()
                
            except Exception as e:
                print(f"Failed to load scraper for {city_name}: {e}")
    
    def scrape_city(self, city: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Scrape permits for a specific city"""
        if city not in self.scrapers:
            raise ValueError(f"No scraper available for city: {city}")
        
        scraper = self.scrapers[city]
        raw_data = scraper.scrape(start_date, end_date)
        validated_data = scraper.validate_data(raw_data)
        
        return validated_data
    
    def get_available_cities(self) -> List[str]:
        """Get list of cities with available scrapers"""
        return list(self.scrapers.keys())

