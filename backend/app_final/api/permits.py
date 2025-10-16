from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List
from app_final.database.db_manager import DatabaseManager
from utils.dependencies import get_db_manager
from app_final.models.permit_models import PermitResponse, StatsResponse

router = APIRouter()


@router.get("/cities", response_model=List[str])
async def get_cities(db_manager: DatabaseManager = Depends(get_db_manager)):
    """Get list of available cities"""
    return db_manager.get_available_cities()


@router.get("/permits", response_model=PermitResponse)
async def search_permits(
        city: Optional[str] = Query(None, description="Filter by city"),
        q: Optional[str] = Query(None, description="Search query"),
        contractor: Optional[str] = Query(None, description="Contractor name"),
        work_class: Optional[str] = Query(None, description="Filter by work class"),
        permit_class: Optional[str] = Query(None, description="Filter by permit class"),
        page: int = Query(1, ge=1, description="Page number"),
        limit: int = Query(20, ge=1, le=100, description="Results per page"),
        db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Search permits with filters"""

    result = db_manager.search_permits(
        city=city,
        query=q,
        contractor=contractor,
        work_class=work_class,
        permit_class=permit_class,
        page=page,
        limit=limit
    )

    return PermitResponse(**result)


@router.get("/stats", response_model=StatsResponse)
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


@router.get("/permits/{permit_id}")
async def get_permit_detail(
        permit_id: str,
        db_manager: DatabaseManager = Depends(get_db_manager)
):
    """Get detailed information for a specific permit"""

    permit = db_manager.get_permit_by_id(permit_id)
    if not permit:
        raise HTTPException(status_code=404, detail="Permit not found")

    return permit