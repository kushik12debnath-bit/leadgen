"""APScheduler-based automation service."""
import asyncio
import csv
import io
import os
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .database import SessionLocal
from . import crud
from .router_engine import resolve_sources
from .scrapers import gmaps, linkedin, facebook, instagram
from .enricher import enrich

SCRAPER_MAP = {
    "gmaps": gmaps.GMapsScraper,
    "linkedin": linkedin.LinkedInScraper,
    "facebook": facebook.FacebookScraper,
    "instagram": instagram.InstagramScraper,
}

scheduler = AsyncIOScheduler()


def _next_run(frequency, interval_value, run_time=None, run_days=None):
    # Local time: APSScheduler CronTrigger fires in the scheduler's (local)
    # timezone, so next_run_at must be computed the same way to be accurate.
    now = datetime.now()
    if frequency == "interval_hours":
        return now + timedelta(hours=interval_value or 24)
    # daily / weekly: next occurrence at the exact run_time
    h, m = _parse_time(run_time)
    candidate = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if candidate <= now:
        candidate = candidate + timedelta(days=1)
    if frequency == "weekly":
        days_map = {"mon":0,"tue":1,"wed":2,"thu":3,"fri":4,"sat":5,"sun":6}
        allowed = [days_map[d.strip()] for d in (run_days or "mon").split(",") if d.strip() in days_map]
        if not allowed:
            allowed = [0]
        # candidate already has the exact time set and is in the future;
        # just advance whole days (time is preserved) until weekday matches.
        while candidate.weekday() not in allowed:
            candidate = candidate + timedelta(days=1)
    return candidate


def _parse_time(s):
    s = (s or "09:00").strip()
    parts = s.split(":")
    h = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 9
    m = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    h = max(0, min(23, h))
    m = max(0, min(59, m))
    return h, m


def _trigger_for(job):
    if job.frequency == "daily":
        h, m = _parse_time(job.run_time)
        return CronTrigger(hour=h, minute=m)
    if job.frequency == "weekly":
        h, m = _parse_time(job.run_time)
        days = (job.run_days or "mon").strip().lower()
        return CronTrigger(day_of_week=days, hour=h, minute=m)
    if job.frequency == "interval_hours":
        return IntervalTrigger(hours=job.interval_value or 24)
    return IntervalTrigger(hours=24)


async def run_job(job_id: int):
    """Execute a scheduled job end-to-end."""
    db = await asyncio.to_thread(SessionLocal)
    log = None
    try:
        job = await asyncio.to_thread(crud.get_job, db, job_id)
        if not job or not job.is_active:
            await asyncio.to_thread(db.close)
            return

        log = await asyncio.to_thread(crud.create_run_log, db, job_id)
        params = {
            "domain": job.domain, "position": job.position,
            "company_name": job.company_name, "location": job.location,
            "radius_km": job.radius_km,
        }
        sources = resolve_sources(job.mode, job.domain, job.company_name, job.selected_sources)

        leads_found = 0
        new_leads = 0
        for src in sources:
            ScraperCls = SCRAPER_MAP.get(src)
            if not ScraperCls:
                continue
            scraper = ScraperCls()
            raw = await scraper.scrape(params)
            for item in raw:
                item.setdefault("domain", job.domain)
                item.setdefault("position", job.position)
                await enrich(item)
                # track new vs existing
                from .crud import find_duplicate
                existing = await asyncio.to_thread(find_duplicate, db, item)
                was_new = existing is None
                await asyncio.to_thread(crud.upsert_lead, db, item)
                leads_found += 1
                if was_new:
                    new_leads += 1

        job.last_run_at = datetime.now()
        job.next_run_at = _next_run(job.frequency, job.interval_value, job.run_time, job.run_days)
        await asyncio.to_thread(db.commit)

        await asyncio.to_thread(crud.finish_run_log, db, log.id, "success",
                               leads_found, new_leads)

        if job.auto_export_csv:
            await _export_csv(db, job)

    except Exception as e:
        if log:
            await asyncio.to_thread(crud.finish_run_log, db, log.id, "failed",
                                   0, 0, str(e))
    finally:
        await asyncio.to_thread(db.close)


async def _export_csv(db, job):
    os.makedirs("data/exports", exist_ok=True)
    rows = await asyncio.to_thread(crud.list_leads, db)
    path = f"data/exports/job_{job.id}_latest.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "position", "company_name", "domain", "location",
                    "sources", "phone", "email", "company_size", "website_url",
                    "has_website", "social_links", "google_rating", "review_count",
                    "digital_presence_score", "is_new", "created_at"])
        for r in rows:
            d = r.to_dict()
            w.writerow([d["id"], d["name"], d["position"], d["company_name"],
                        d["domain"], d["location"], ",".join(d["sources"]), d["phone"],
                        d["email"], d["company_size"], d["website_url"], d["has_website"],
                        d["social_links"], d["google_rating"], d["review_count"],
                        d["digital_presence_score"], d["is_new"], d["created_at"]])


def schedule_job(job, db=None):
    """Register (or re-register) a job with the scheduler at its exact time.

    Persists job.next_run_at so the UI can show when it will fire next.
    """
    if not job.is_active:
        job.next_run_at = None
        if db is not None:
            db.commit()
        return
    trigger = _trigger_for(job)
    next_at = _next_run(job.frequency, job.interval_value, job.run_time, job.run_days)
    job.next_run_at = next_at
    scheduler.add_job(run_job, trigger, args=[job.id],
                     id=f"job_{job.id}", replace_existing=True,
                     next_run_time=next_at)
    if db is not None:
        db.commit()


def remove_job(job_id):
    jid = f"job_{job_id}"
    if scheduler.get_job(jid):
        scheduler.remove_job(jid)


def start_scheduler():
    scheduler.start()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)


async def bootstrap_jobs():
    """Re-schedule active jobs on startup."""
    db = await asyncio.to_thread(SessionLocal)
    try:
        jobs = await asyncio.to_thread(crud.list_jobs, db)
        for j in jobs:
            if j.is_active:
                await asyncio.to_thread(schedule_job, j, db)
    finally:
        await asyncio.to_thread(db.close)