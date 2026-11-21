"""FastAPI application entrypoint with APScheduler lifespan."""
import sys
import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional, List
import csv
import io

from .database import init_db, get_db, SessionLocal
from . import crud, models, schemas
from .router_engine import resolve_sources
from .scrapers import gmaps, linkedin, facebook, instagram
from .enricher import enrich
from .scheduler_service import (
    scheduler, start_scheduler, shutdown_scheduler, bootstrap_jobs,
    schedule_job, remove_job, run_job,
)

SCRAPER_MAP = {
    "gmaps": gmaps.GMapsScraper,
    "linkedin": linkedin.LinkedInScraper,
    "facebook": facebook.FacebookScraper,
    "instagram": instagram.InstagramScraper,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    await bootstrap_jobs()
    yield
    shutdown_scheduler()


BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Multi-Platform Lead Intelligence (Phase 1)", version="1.0.0",
              lifespan=lifespan)

if STATIC_DIR.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR)) if TEMPLATES_DIR.exists() else None


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    if templates is None:
        return HTMLResponse("<h1>Templates not found</h1>")
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/search/run")
async def instant_run(req: schemas.SearchRunRequest):
    try:
        sources = resolve_sources(req.mode, req.domain, req.company_name, req.selected_sources)
    except ValueError as e:
        raise HTTPException(400, str(e))

    params = {
        "domain": req.domain, "position": req.position,
        "company_name": req.company_name, "location": req.location,
        "radius_km": req.radius_km,
    }

    db = await asyncio.to_thread(SessionLocal)
    leads_found = 0
    new_leads = 0
    try:
        for src in sources:
            ScraperCls = SCRAPER_MAP.get(src)
            if not ScraperCls:
                continue
            scraper = ScraperCls()
            raw = await scraper.scrape(params)
            for item in raw:
                item.setdefault("domain", req.domain)
                item.setdefault("position", req.position)
                await enrich(item)
                from .crud import find_duplicate
                existing = await asyncio.to_thread(find_duplicate, db, item)
                was_new = existing is None
                await asyncio.to_thread(crud.upsert_lead, db, item)
                leads_found += 1
                if was_new:
                    new_leads += 1
    finally:
        await asyncio.to_thread(db.close)

    return {"status": "completed", "sources": sources,
            "leads_found": leads_found, "new_leads_added": new_leads}


@app.post("/api/jobs", response_model=schemas.JobOut)
async def create_job(req: schemas.JobCreateRequest, db: Session = Depends(get_db)):
    try:
        sources = resolve_sources(req.mode, req.domain, req.company_name, req.selected_sources)
    except ValueError as e:
        raise HTTPException(400, str(e))

    # For auto mode, store resolved sources for transparency
    selected = req.selected_sources if req.mode == "custom" else sources

    data = req.model_dump()
    data["selected_sources"] = selected
    job = crud.create_job(db, data)
    schedule_job(job, db)
    return job.to_dict()


@app.get("/api/jobs", response_model=List[schemas.JobOut])
def get_jobs(db: Session = Depends(get_db)):
    jobs = crud.list_jobs(db)
    return [j.to_dict() for j in jobs]


@app.patch("/api/jobs/{job_id}/toggle", response_model=schemas.JobOut)
def toggle_job(job_id: int, db: Session = Depends(get_db)):
    job = crud.toggle_job(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.is_active:
        schedule_job(job, db)
    else:
        remove_job(job_id)
        schedule_job(job, db)  # persists next_run_at = None when inactive
    return job.to_dict()


@app.patch("/api/jobs/{job_id}", response_model=schemas.JobOut)
def update_job(job_id: int, req: schemas.JobUpdateRequest, db: Session = Depends(get_db)):
    job = crud.get_job(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    data = req.model_dump(exclude_unset=True)
    if "mode" in data or "selected_sources" in data:
        mode = data.get("mode", job.mode)
        sources = data.get("selected_sources", job.selected_sources)
        try:
            resolve_sources(mode, data.get("domain", job.domain),
                            data.get("company_name", job.company_name), sources)
        except ValueError as e:
            raise HTTPException(400, str(e))
    for k, v in data.items():
        if hasattr(job, k):
            setattr(job, k, v)
    db.commit()
    db.refresh(job)
    # re-register with the new frequency / exact time
    if job.is_active:
        schedule_job(job, db)
    else:
        remove_job(job_id)
        schedule_job(job, db)
    return job.to_dict()


@app.delete("/api/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_job(db, job_id)
    if not ok:
        raise HTTPException(404, "Job not found")
    remove_job(job_id)
    return {"status": "deleted"}


@app.get("/api/jobs/{job_id}/runs", response_model=List[schemas.JobRunLogOut])
def get_job_runs(job_id: int, db: Session = Depends(get_db)):
    logs = crud.list_run_logs(db, job_id)
    return [l.to_dict() for l in logs]


@app.post("/api/jobs/{job_id}/run")
async def run_job_now(job_id: int, db: Session = Depends(get_db)):
    job = crud.get_job(db, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    await run_job(job_id)
    return {"status": "completed"}


@app.get("/api/leads", response_model=List[schemas.LeadOut])
def get_leads(
    db: Session = Depends(get_db),
    source: Optional[str] = Query(None),
    has_website: Optional[bool] = Query(None),
    min_score: Optional[int] = Query(None),
    max_score: Optional[int] = Query(None),
    company_size: Optional[str] = Query(None),
    is_new: Optional[bool] = Query(None),
    limit: int = Query(1000),
):
    rows = crud.list_leads(db, source=source, has_website=has_website,
                           min_score=min_score, max_score=max_score,
                           company_size=company_size, is_new=is_new, limit=limit)
    return [r.to_dict() for r in rows]


@app.delete("/api/leads")
def clear_leads(db: Session = Depends(get_db)):
    crud.delete_all_leads(db)
    return {"status": "cleared"}


def _local(utc_dt):
    """Convert naive-UTC DB datetime to the machine's local timezone."""
    if utc_dt is None:
        return None
    return utc_dt.replace(tzinfo=timezone.utc).astimezone()


CSV_HEADERS = ["generated_date", "generated_time",
               "id", "name", "position", "company_name", "domain", "location",
               "sources", "phone", "email", "company_size", "website_url",
               "has_website", "social_links", "google_rating", "review_count",
               "digital_presence_score", "is_new", "lead_generated_at"]


@app.get("/api/leads/export")
def export_leads(
    db: Session = Depends(get_db),
    source: Optional[str] = Query(None),
    has_website: Optional[bool] = Query(None),
    min_score: Optional[int] = Query(None),
    max_score: Optional[int] = Query(None),
    company_size: Optional[str] = Query(None),
    is_new: Optional[bool] = Query(None),
    only_new: bool = Query(True, description="Export only leads not yet exported"),
    mark_exported: bool = Query(True, description="Mark exported new leads as existing"),
):
    """CSV export of leads with their generation date + time.

    Default (only_new=true) exports ONLY newly generated leads, then marks
    them as no longer new - so each download contains only the leads
    generated since the previous export.
    """
    if only_new:
        is_new = True
    rows = crud.list_leads(db, source=source, has_website=has_website,
                           min_score=min_score, max_score=max_score,
                           company_size=company_size, is_new=is_new, limit=100000)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(CSV_HEADERS)
    for r in rows:
        loc = _local(r.created_at)
        d = r.to_dict()
        w.writerow([
            loc.strftime("%Y-%m-%d") if loc else "",
            loc.strftime("%H:%M:%S") if loc else "",
            d["id"], d["name"], d["position"], d["company_name"], d["domain"],
            d["location"], ",".join(d["sources"]), d["phone"], d["email"],
            d["company_size"], d["website_url"], d["has_website"],
            d["social_links"], d["google_rating"], d["review_count"],
            d["digital_presence_score"], d["is_new"],
            loc.isoformat() if loc else "",
        ])
    buf.seek(0)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    prefix = "new_leads" if only_new else "leads"
    filename = f"{prefix}_{stamp}.csv"

    if only_new and mark_exported and rows:
        crud.mark_leads_exported(db, [r.id for r in rows])

    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition":
                                      f"attachment; filename={filename}"})


@app.get("/health")
def health():
    return {"status": "ok"}