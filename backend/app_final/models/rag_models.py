from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class ClientSelection(BaseModel):
    client_ids: Optional[List[int]] = None      # None => all active
    status: Optional[str] = "active"            # filter clients by status if needed


class ClientRAGRequest(BaseModel):
    # Mode 1: Ad-hoc query for all selected clients (overrides saved query)
    query: Optional[str] = None

    # Mode 2: Use per-client saved queries/filters in DB (rag_query, rag_filters_json)
    use_client_prefs: Optional[bool] = True

    selection: Optional[ClientSelection] = ClientSelection()

    # Global filters applied in addition to client-specific ones
    filters: Optional[Dict[str, Any]] = None

    # NEW: Keyword include/exclude filtering
    keywords_include: Optional[List[str]] = None  # Must contain at least one (OR logic)
    keywords_exclude: Optional[List[str]] = None  # Exclude if contains any (OR logic)

    # NEW: Search mode
    search_mode: Optional[str] = "semantic_only"  # "semantic_only" or "full_breakdown"

    # per-client limits & searching knobs
    per_client_top_k: Optional[int] = 20
    oversample: Optional[int] = 10
    exclusive: Optional[bool] = True  # assign each permit to at most one client

    # email
    dry_run: Optional[bool] = True  # preview by default

class ClientRAGPreviewResponse(BaseModel):
    success: bool
    summary: Dict[str, Any]
    assignments: Dict[str, Any]  # email -> {"client": {...}, "count": int, "samples": [...]}

class ClientRAGSendResponse(BaseModel):
    success: bool
    summary: Dict[str, Any]
    results: Dict[str, Any]

class RAGSearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 20
    oversample: Optional[int] = 5
    # filters supports:
    # city, permit_type, permit_class_mapped, work_class, status (all lists)
    # issued_date_from, issued_date_to, applied_date_from, applied_date_to (YYYY-MM-DD)
    filters: Optional[Dict[str, Any]] = None

class RAGSearchResponse(BaseModel):
    success: bool
    count: int
    results: List[Dict[str, Any]]

class RAGStatusResponse(BaseModel):
    loaded: bool
    vectors: int
    dim: Optional[int]
    index_path: str