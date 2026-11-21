"""CRUD helpers with deduplication."""
from sqlalchemy.orm import Session
from .models import Lead, ScheduledJob, JobRunLog


def _norm(v):
    return (v or "").strip().lower() if isinstance(v, str) else v


def find_duplicate(db: Session, lead: dict) -> Lead:
    phone = lead.get("phone")
    email = lead.get("email")
    company = lead.get("company_name")
    if phone:
        r = db.query(Lead).filter(Lead.phone == phone).first()
        if r:
            return r
    if email:
        r = db.query(Lead).filter(Lead.email == email).first()
        if r:
            return r
    if company:
        r = db.query(Lead).filter(Lead.company_name == company,
                                   Lead.location == lead.get("location")).first()
        if r:
            return r
    return None


def upsert_lead(db: Session, lead: dict) -> Lead:
    existing = find_duplicate(db, lead)
    if existing:
        for k, v in lead.items():
            if v is not None and v != "" and hasattr(existing, k):
                # merge sources list
                if k == "sources" and isinstance(v, list):
                    cur = existing.sources or []
                    existing.sources = list(set(cur + v))
                elif k == "social_links" and isinstance(v, dict):
                    cur = existing.social_links or {}
                    cur.update(v)
                    existing.social_links = cur
                else:
                    setattr(existing, k, v)
        existing.is_new = False
        db.commit()
        db.refresh(existing)
        return existing
    obj = Lead(**{k: v for k, v in lead.items() if hasattr(Lead, k)})
    obj.is_new = True
    db.add(obj)
    try:
        db.commit()
    except Exception:
        db.rollback()
        existing = find_duplicate(db, lead)
        if existing:
            return existing
        db.add(obj)
        db.commit()
    db.refresh(obj)
    return obj


def delete_all_leads(db):
    db.query(Lead).delete()
    db.commit()


def mark_leads_exported(db, ids):
    """Mark leads as no longer 'new' after they have been exported to CSV."""
    if not ids:
        return 0
    n = db.query(Lead).filter(Lead.id.in_(ids)).update(
        {"is_new": False}, synchronize_session=False)
    db.commit()
    return n


def list_leads(db, source=None, has_website=None, min_score=None, max_score=None,
               company_size=None, is_new=None, limit=1000):
    q = db.query(Lead)
    if source:
        # source filter: lead's sources list contains source
        q = q.filter(Lead.sources.contains([source]) if False else Lead.sources.isnot(None))
        # fallback: filter in python below
    if has_website is not None:
        q = q.filter(Lead.has_website == has_website)
    if min_score is not None:
        q = q.filter(Lead.digital_presence_score >= min_score)
    if max_score is not None:
        q = q.filter(Lead.digital_presence_score <= max_score)
    if company_size:
        q = q.filter(Lead.company_size == company_size)
    if is_new is not None:
        q = q.filter(Lead.is_new == is_new)
    rows = q.order_by(Lead.created_at.desc()).limit(limit).all()
    if source:
        rows = [r for r in rows if r.sources and source in r.sources]
    return rows


def create_job(db, data: dict) -> ScheduledJob:
    job = ScheduledJob(**{k: v for k, v in data.items() if hasattr(ScheduledJob, k)})
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def list_jobs(db):
    return db.query(ScheduledJob).order_by(ScheduledJob.created_at.desc()).all()


def get_job(db, job_id):
    return db.query(ScheduledJob).filter(ScheduledJob.id == job_id).first()


def toggle_job(db, job_id):
    job = get_job(db, job_id)
    if not job:
        return None
    job.is_active = not job.is_active
    db.commit()
    db.refresh(job)
    return job


def delete_job(db, job_id):
    job = get_job(db, job_id)
    if not job:
        return False
    db.delete(job)
    db.commit()
    return True


def create_run_log(db, job_id):
    log = JobRunLog(job_id=job_id, status="running")
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def finish_run_log(db, log_id, status, leads_found=0, new_leads=0, error=None):
    log = db.query(JobRunLog).filter(JobRunLog.id == log_id).first()
    if not log:
        return
    from datetime import datetime
    log.finished_at = datetime.utcnow()
    log.status = status
    log.leads_found = leads_found
    log.new_leads_added = new_leads
    log.error_message = error
    db.commit()


def list_run_logs(db, job_id=None, limit=50):
    q = db.query(JobRunLog)
    if job_id:
        q = q.filter(JobRunLog.job_id == job_id)
    return q.order_by(JobRunLog.started_at.desc()).limit(limit).all()