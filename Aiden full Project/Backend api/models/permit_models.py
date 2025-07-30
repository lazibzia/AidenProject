from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class PermitBase(BaseModel):
    city: str
    permit_num: str
    address: Optional[str] = None
    contractor_name: Optional[str] = None
    valuation: Optional[float] = None
    permit_fee: Optional[float] = None
    date_issued: Optional[str] = None
    neighborhood: Optional[str] = None
    class_: Optional[str] = None
    units: Optional[int] = None
    description: Optional[str] = None
    status: Optional[str] = None

class Permit(PermitBase):
    id: int
    created_at: datetime
    updated_at: datetime

class PermitResponse(BaseModel):
    permits: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    pages: int

class StatsResponse(BaseModel):
    city: Optional[str] = None
    stats: Dict[str, Any]
    yearly_data: List[Dict[str, Any]]
    valuation_distribution: List[Dict[str, Any]]

class CityConfig(BaseModel):
    display_name: str
    timezone: str
    scraper_class: str
    base_url: str
    residential_only: bool
    fields_mapping: Dict[str, str]

class ScrapeRequest(BaseModel):
    city: str
    mode: str = "daily"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ScrapeResponse(BaseModel):
    success: bool
    city: str
    fetched: int
    inserted: int
    message: str


