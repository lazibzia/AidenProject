from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class PermitResponse(BaseModel):
    permits: List[Dict[str, Any]]
    total: int
    page: int
    limit: int
    has_next: bool
    has_prev: bool

class StatsResponse(BaseModel):
    city: Optional[str]
    stats: Dict[str, Any]
    yearly_data: List[Dict[str, Any]]
    valuation_distribution: List[Dict[str, Any]]

class CityConfig(BaseModel):
    name: str
    base_url: str
    search_endpoint: str
    fields_mapping: Dict[str, str]
    date_format: str
    pagination_params: Dict[str, Any]