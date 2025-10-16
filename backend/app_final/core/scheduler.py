from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler()


def setup_default_schedules():
    """Setup default schedules for scraping and automation"""
    from app_final.services.automation_service import run_automated_workflow
    from config.cities import CITY_CONFIGS

    # Set up default daily scraping for all cities at 6 AM
    for city in CITY_CONFIGS.keys():
        scheduler.add_job(
            lambda c=city: scheduled_scrape_city(c),
            CronTrigger(hour=6, minute=0),
            id=f"scrape_{city}",
            replace_existing=True
        )

    # Start the 4-hour automation cycle
    scheduler.add_job(
        run_automated_workflow,
        IntervalTrigger(hours=4),
        id="automated_workflow",
        replace_existing=True,
        next_run_time=datetime.now() + timedelta(minutes=5)
    )

    logger.info("Default schedules configured")


def scheduled_scrape_city(city: str):
    """Background task for scheduled scraping"""
    try:
        from database.db_manager import DatabaseManager
        from scrapers.scraper import ScraperManager

        logger.info(f"🕐 Scheduled scrape started for {city}")

        today = datetime.today().date()
        start_date = end_date = today.strftime('%Y-%m-%d')

        db_manager = DatabaseManager()
        scraper_manager = ScraperManager()

        # Scrape permits
        permits_data = scraper_manager.scrape_city(city, start_date, end_date)

        # Insert into database
        inserted_count = db_manager.insert_permits(city, permits_data)

        logger.info(f"✅ Scheduled scrape completed for {city}: {inserted_count} new permits")

    except Exception as e:
        logger.error(f"❌ Scheduled scrape failed for {city}: {e}")