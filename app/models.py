"""SQLAlchemy ORM models."""
import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=True)
    position = Column(String(200), nullable=True)
    company_name = Column(String(300), nullable=True, index=True)
    domain = Column(String(100), nullable=True)
    location = Column(String(300), nullable=True)
    sources = Column(JSON, default=list)          # ["gmaps","linkedin",...]
    phone = Column(String(50), nullable=True, index=True)
    email = Column(String(200), nullable=True, index=True)
    company_size = Column(String(100), nullable=True)
    website_url = Column(String(500), nullable=True)
    has_website = Column(Boolean, default=False)
    social_links = Column(JSON, default=dict)      # {"facebook": url, ...}
    google_rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=True)
    digital_presence_score = Column(Integer, default=0)
    is_new = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "position": self.position,
            "company_name": self.company_name,
            "domain": self.domain,
            "location": self.location,
            "sources": self.sources or [],
            "phone": self.phone,
            "email": self.email,
            "company_size": self.company_size,
            "website_url": self.website_url,
            "has_website": bool(self.has_website),
            "social_links": self.social_links or {},
            "google_rating": self.google_rating,
            "review_count": self.review_count,
            "digital_presence_score": self.digital_presence_score or 0,
            "is_new": bool(self.is_new),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ScheduledJob(Base):
    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(200), nullable=False)
    mode = Column(String(20), nullable=False)            # auto | custom
    selected_sources = Column(JSON, default=list)        # for custom mode
    domain = Column(String(100), nullable=True)
    position = Column(String(200), nullable=True)
    company_name = Column(String(300), nullable=True)
    location = Column(String(300), nullable=True)
    radius_km = Column(Integer, default=10)
    frequency = Column(String(30), nullable=False)      # daily | weekly | interval_hours
    interval_value = Column(Integer, default=24)         # hours for interval_hours
    run_time = Column(String(10), default="09:00")       # exact time HH:MM (24h)
    run_days = Column(String(50), default="mon")          # for weekly: mon,tue,...
    auto_export_csv = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    runs = relationship("JobRunLog", back_populates="job", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "job_name": self.job_name,
            "mode": self.mode,
            "selected_sources": self.selected_sources or [],
            "domain": self.domain,
            "position": self.position,
            "company_name": self.company_name,
            "location": self.location,
            "radius_km": self.radius_km,
            "frequency": self.frequency,
            "interval_value": self.interval_value,
            "run_time": self.run_time or "09:00",
            "run_days": self.run_days or "mon",
            "auto_export_csv": bool(self.auto_export_csv),
            "is_active": bool(self.is_active),
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class JobRunLog(Base):
    __tablename__ = "job_run_logs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scheduled_jobs.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(30), default="running")       # running | success | failed
    leads_found = Column(Integer, default=0)
    new_leads_added = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    job = relationship("ScheduledJob", back_populates="runs")

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "status": self.status,
            "leads_found": self.leads_found or 0,
            "new_leads_added": self.new_leads_added or 0,
            "error_message": self.error_message,
        }