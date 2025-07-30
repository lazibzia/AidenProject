from fastapi import FastAPI, Request, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Optional, List
import uvicorn
from datetime import datetime, timedelta
from fastapi.middleware.cors import CORSMiddleware
# Import our modular components
from database.db_manager import DatabaseManager
from scrapers.scraper import ScraperManager
from models.permit_models import PermitResponse, StatsResponse, CityConfig
from config.cities import CITY_CONFIGS
from utils.dependencies import get_db_manager, get_scraper_manager

app = FastAPI(
    title="Multi-City Permits Dashboard",
    description="Unified dashboard for permits across multiple cities",
    version="2.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# ===== DASHBOARD ROUTES =====
@app.get("/", response_class=JSONResponse)
async def dashboard(
    request: Request,
    city: Optional[str] = Query(None, description="Filter by city"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Main dashboard - can show all cities or filter by specific city"""
    
    # Get available cities
    cities = db_manager.get_available_cities()
    
    # Get stats for selected city or all cities
    if city and city in cities:
        stats = db_manager.get_city_stats(city)
        recent_permits = db_manager.get_recent_permits(city, limit=10)
        top_contractors = db_manager.get_top_contractors(city, limit=10)
        selected_city = city
    else:
        stats = db_manager.get_overall_stats()
        recent_permits = db_manager.get_recent_permits(limit=10)
        top_contractors = db_manager.get_top_contractors(limit=10)
        selected_city = None
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_permits": recent_permits,
        "top_contractors": top_contractors,
        "cities": cities,
        "selected_city": selected_city
    })

@app.get("/city/{city_name}", response_class=JSONResponse)
async def city_dashboard(
    request: Request,
    city_name: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """City-specific dashboard"""
    
    if city_name not in CITY_CONFIGS:
        raise HTTPException(status_code=404, detail=f"City '{city_name}' not found")
    
    stats = db_manager.get_city_stats(city_name)
    recent_permits = db_manager.get_recent_permits(city_name, limit=10)
    top_contractors = db_manager.get_top_contractors(city_name, limit=10)
    
    return templates.TemplateResponse("city_dashboard.html", {
        "request": request,
        "city": city_name,
        "city_config": CITY_CONFIGS[city_name],
        "stats": stats,
        "recent_permits": recent_permits,
        "top_contractors": top_contractors
    })

# ===== API ROUTES =====
@app.get("/api/cities", response_model=List[str])
async def get_cities(db_manager: DatabaseManager = Depends(get_db_manager)):
    """Get list of available cities"""
    return db_manager.get_available_cities()

@app.get("/api/permits", response_model=PermitResponse)
async def search_permits(
    city: Optional[str] = Query(None, description="Filter by city"),
    q: Optional[str] = Query(None, description="Search query"),
    contractor: Optional[str] = Query(None, description="Contractor name"),
    min_valuation: Optional[float] = Query(None, description="Minimum valuation"),
    max_valuation: Optional[float] = Query(None, description="Maximum valuation"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Search permits with filters"""
    
    result = db_manager.search_permits(
        city=city,
        query=q,
        contractor=contractor,
        min_valuation=min_valuation,
        max_valuation=max_valuation,
        page=page,
        limit=limit
    )
    
    response = PermitResponse(**result)
    print("API Response:", response)
    return response

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(
    city: Optional[str] = Query(None, description="Filter by city"),
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get statistics for all cities or specific city"""
    
    if city:
        stats = db_manager.get_city_stats(city)
        yearly_data = db_manager.get_yearly_stats(city)
        valuation_dist = db_manager.get_valuation_distribution(city)
    else:
        stats = db_manager.get_overall_stats()
        yearly_data = db_manager.get_yearly_stats()
        valuation_dist = db_manager.get_valuation_distribution()
    
    return StatsResponse(
        city=city,
        stats=stats,
        yearly_data=yearly_data,
        valuation_distribution=valuation_dist
    )

@app.get("/api/permits/{permit_id}")
async def get_permit_detail(
    permit_id: str,
    db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get detailed information for a specific permit"""
    
    permit = db_manager.get_permit_by_id(permit_id)
    if not permit:
        raise HTTPException(status_code=404, detail="Permit not found")
    
    return permit

# ===== SCRAPING ROUTES =====
@app.post("/api/scrape")
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

@app.post("/api/scrape-all")
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

# ===== SCHEDULER ROUTES =====
@app.post("/api/schedule/update")
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
        scheduler.add_job(
            lambda c=city: scheduled_scrape(c, db_manager, ScraperManager()),
            CronTrigger(hour=hour, minute=minute),
            id=f"scrape_{city}",
            replace_existing=True
        )
    
    return {
        "message": f"Schedule updated: {hour:02d}:{minute:02d} for cities: {', '.join(cities)}"
    }

# ===== BACKGROUND TASKS =====
def scheduled_scrape(city: str, db_manager: DatabaseManager, scraper_manager: ScraperManager):
    """Background task for scheduled scraping"""
    
    try:
        print(f"🕐 Scheduled scrape started for {city}")
        
        today = datetime.today().date()
        start_date = end_date = today.strftime('%Y-%m-%d')
        
        # Scrape permits
        permits_data = scraper_manager.scrape_city(city, start_date, end_date)
        
        # Insert into database
        inserted_count = db_manager.insert_permits(city, permits_data)
        
        print(f"✅ Scheduled scrape completed for {city}: {inserted_count} new permits")
        
    except Exception as e:
        print(f"❌ Scheduled scrape failed for {city}: {e}")

# ===== STARTUP =====
@app.on_event("startup")
async def startup_event():
    """Initialize database and default schedules"""
    
    db_manager = DatabaseManager()
    db_manager.initialize_database()
    
    # Set up default daily scraping for all cities at 6 AM
    for city in CITY_CONFIGS.keys():
        scheduler.add_job(
            lambda c=city: scheduled_scrape(c, DatabaseManager(), ScraperManager()),
            CronTrigger(hour=6, minute=0),
            id=f"scrape_{city}",
            replace_existing=True
        )


    
    print("🚀 Multi-City Permits Dashboard started!")
    print(f"📊 Configured cities: {', '.join(CITY_CONFIGS.keys())}")

if __name__ == "__main__":
    uvicorn.run(app, host='0.0.0.0', port=5000, reload=True)