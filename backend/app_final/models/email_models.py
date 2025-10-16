from pydantic import BaseModel
from typing import Optional, Dict, Any

class EmailRequest(BaseModel):
    days_back: Optional[int] = 30
    dry_run: Optional[bool] = False

class EmailResponse(BaseModel):
    success: bool
    message: str
    summary: Dict[str, Any]
    performance: Dict[str, float]
    timestamp: str

class PreviewResponse(BaseModel):
    success: bool
    preview: Dict[str, Any]