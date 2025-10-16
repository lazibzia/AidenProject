from fastapi import APIRouter, Request, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from app_final.database.db_manager import DatabaseManager
from utils.dependencies import get_db_manager
from config.cities import CITY_CONFIGS

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
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


@router.get("/city/{city_name}", response_class=HTMLResponse)
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