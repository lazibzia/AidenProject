from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from datetime import datetime, timedelta
from app_final.database.db_manager import DatabaseManager
from app_final.scrapers.scraper import ScraperManager
from utils.dependencies import get_db_manager, get_scraper_manager
from config.cities import CITY_CONFIGS
from app_final.core.scheduler import scheduler

router = APIRouter()


@router.post("/scrape")
async def trigger_scrape(
        city: str = Query(..., description="City to scrape"),
        mode: str = Query("daily", enum=["daily", "weekly", "monthly", "custom"]),
        start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
        db_manager: DatabaseManager = Depends(get_db_manager),
        scraper_manager: ScraperManager = Depends(get_scraper_manager)
):
    """Trigger scraping for a specific city"""

    if city not in CITY_CONFIGS:
        raise HTTPException(status_code=404, detail=f"City '{city}' not configured")

    try:
        # Calculate date range
        today = datetime.today().date()
        if mode == "daily":
            start_date = end_date = today.strftime('%Y-%m-%d')
        elif mode == "weekly":
            start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif mode == "monthly":
            start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
        elif mode == "custom":
            if not start_date or not end_date:
                raise HTTPException(status_code=400, detail="Custom mode requires start_date and end_date")

        # Scrape data
        permits_data = scraper_manager.scrape_city(city, start_date, end_date)

        # Insert into database
        inserted_count = db_manager.insert_permits(city, permits_data)

        return {
            "success": True,
            "city": city,
            "fetched": len(permits_data),
            "inserted": inserted_count,
            "message": f"Scraped {city}: {inserted_count} new permits added"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")


@router.post("/scrape-all")
async def scrape_all_cities(
        mode: str = Query("daily", enum=["daily", "weekly", "monthly"]),
        db_manager: DatabaseManager = Depends(get_db_manager),
        scraper_manager: ScraperManager = Depends(get_scraper_manager)
):
    """Scrape all configured cities"""

    results = {}

    for city_name in CITY_CONFIGS.keys():
        try:
            # Calculate date range
            today = datetime.today().date()
            if mode == "daily":
                start_date = end_date = today.strftime('%Y-%m-%d')
            elif mode == "weekly":
                start_date = (today - timedelta(days=7)).strftime('%Y-%m-%d')
                end_date = today.strftime('%Y-%m-%d')
            elif mode == "monthly":
                start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
                end_date = today.strftime('%Y-%m-%d')

            # Scrape and insert
            permits_data = scraper_manager.scrape_city(city_name, start_date, end_date)
            inserted_count = db_manager.insert_permits(city_name, permits_data)

            results[city_name] = {
                "success": True,
                "fetched": len(permits_data),
                "inserted": inserted_count
            }

        except Exception as e:
            results[city_name] = {
                "success": False,
                "error": str(e)
            }

    return {
        "message": "Bulk scraping completed",
        "results": results
    }


@router.post("/schedule/update")
async def update_schedule(
        hour: int = Query(..., ge=0, le=23),
        minute: int = Query(..., ge=0, le=59),
        cities: List[str] = Query(..., description="Cities to schedule"),
        db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Update scraping schedule"""

    # Validate cities
    for city in cities:
        if city not in CITY_CONFIGS:
            raise HTTPException(status_code=400, detail=f"City '{city}' not configured")

    # Save schedule to database
    db_manager.update_schedule_settings(hour, minute, cities)

    # Update scheduler
    scheduler.remove_all_jobs()
    for city in cities:
        from app_final.core.scheduler import scheduled_scrape_city
        scheduler.add_job(
            lambda c=city: scheduled_scrape_city(c),
            'cron',
            hour=hour,
            minute=minute,
            id=f"scrape_{city}",
            replace_existing=True
        )

    return {
        "message": f"Schedule updated: {hour:02d}:{minute:02d} for cities: {', '.join(cities)}"
    }