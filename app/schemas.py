"""Pydantic schemas."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SearchRunRequest(BaseModel):
    mode: str = Field(..., pattern="^(auto|custom)$")
    domain: Optional[str] = None
    position: Optional[str] = None
    company_name: Optional[str] = None
    location: str
    radius_km: int = 10
    max_results: int = 20
    selected_sources: Optional[List[str]] = None   # for custom mode


class JobCreateRequest(BaseModel):
    job_name: str
    mode: str = Field(..., pattern="^(auto|custom)$")
    selected_sources: Optional[List[str]] = None
    domain: Optional[str] = None
    position: Optional[str] = None
    company_name: Optional[str] = None
    location: str
    radius_km: int = 10
    frequency: str = Field(..., pattern="^(daily|weekly|interval_hours)$")
    interval_value: int = 24
    run_time: Optional[str] = "09:00"
    run_days: Optional[str] = "mon"
    auto_export_csv: bool = False


class JobUpdateRequest(BaseModel):
    """Partial update for an existing scheduled job."""
    job_name: Optional[str] = None
    mode: Optional[str] = Field(None, pattern="^(auto|custom)$")
    selected_sources: Optional[List[str]] = None
    domain: Optional[str] = None
    position: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    radius_km: Optional[int] = None
    frequency: Optional[str] = Field(None, pattern="^(daily|weekly|interval_hours)$")
    interval_value: Optional[int] = None
    run_time: Optional[str] = None
    run_days: Optional[str] = None
    auto_export_csv: Optional[bool] = None
    is_active: Optional[bool] = None


class LeadOut(BaseModel):
    id: int
    name: Optional[str] = None
    position: Optional[str] = None
    company_name: Optional[str] = None
    domain: Optional[str] = None
    location: Optional[str] = None
    sources: List[str] = []
    phone: Optional[str] = None
    email: Optional[str] = None
    company_size: Optional[str] = None
    website_url: Optional[str] = None
    has_website: bool = False
    social_links: Dict[str, Any] = {}
    google_rating: Optional[float] = None
    review_count: Optional[int] = None
    digital_presence_score: int = 0
    is_new: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class JobOut(BaseModel):
    id: int
    job_name: str
    mode: str
    selected_sources: List[str] = []
    domain: Optional[str] = None
    position: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    radius_km: int = 10
    frequency: str
    interval_value: int = 24
    run_time: Optional[str] = "09:00"
    run_days: Optional[str] = "mon"
    auto_export_csv: bool = False
    is_active: bool = True
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    created_at: Optional[str] = None


class JobRunLogOut(BaseModel):
    id: int
    job_id: int
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    status: str
    leads_found: int = 0
    new_leads_added: int = 0
    error_message: Optional[str] = None