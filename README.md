# LeadGen Intelligence

**Multi-platform lead generation & digital presence scoring — local-first, zero-cost.**

A production-grade lead-gen dashboard that discovers businesses across **Google Maps, LinkedIn, Facebook and Instagram**, enriches them with contact data, scores their digital presence 0–100, and exports clean CSVs — on a schedule you define down to the exact minute.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Highlights

| Feature | Description |
|---|---|
| **Smart router** | `Auto` mode classifies your query: Local/SMB → Google Maps, B2B/Industrial → LinkedIn |
| **Custom dispatch** | Pick any combination of Google Maps / LinkedIn / Facebook / Instagram |
| **Digital presence score** | Every lead scored 0–100 from website, HTTPS, socials, rating & reviews |
| **New-leads-only CSV** | Exports **only leads generated since the last download**, each row stamped with its generation **date + time** |
| **Exact-time automation** | Daily / weekly / every-N-hours jobs at an exact `HH:MM` you choose |
| **Auto CSV export** | Scheduled jobs can write `data/exports/job_<id>_latest.csv` after each run |
| **Dedup engine** | Phone → email → company+location matching; merged sources, never duplicated |
| **Fully offline UI** | Self-hosted Alpine.js + hand-written CSS — no CDN, works with no internet |
| **Zero cost** | No API keys, no paid tiers, no external services. Everything runs locally |

---

## Quick start (Windows)

```cmd
cd leadgen
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then open **http://127.0.0.1:8000** — or double-click `start_multi.bat`.

> Requires Python 3.11+ with `pip install -r requirements.txt`

### Other platforms

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000   # macOS / Linux
```

---

## Using the dashboard

1. **Step 01 — Discover** — choose `Auto` (smart route) or `Custom` (tick platforms), enter domain + location, hit **Run Scrape**.
2. **Step 02 — Refine & Export** — filter by source, website, company size, score range or new/existing, then:
   - **⬇ New Leads CSV** → only the leads generated since the last export, with `generated_date`, `generated_time` and `lead_generated_at` columns. Exported rows are then marked as existing, so your next download only ever contains fresh leads.
   - **⬇ All CSV** → the entire database.
3. **Step 03 — Results** — leads table with source badges, digital-score bars and generation timestamps.
4. **Step 04 — Automate** — create a job with a **frequency** and an **exact time (HH:MM)**; the *Next Run* column always shows precisely when it fires.

---

## API

Interactive docs: **http://127.0.0.1:8000/docs**

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/search/run` | Run a scrape (`mode`, `domain`, `location`, `selected_sources`) |
| `GET` | `/api/leads` | List leads (filters: `source`, `has_website`, `min_score`, `max_score`, `company_size`, `is_new`) |
| `GET` | `/api/leads/export` | CSV export (`only_new`, `mark_exported` + all filters) |
| `DELETE` | `/api/leads` | Clear all leads |
| `POST` | `/api/jobs` | Create scheduled job (`frequency`, `run_time`, `run_days`) |
| `GET` | `/api/jobs` | List jobs with `next_run_at` |
| `PATCH` | `/api/jobs/{id}` | Update a job (re-schedules automatically) |
| `PATCH` | `/api/jobs/{id}/toggle` | Activate / pause |
| `POST` | `/api/jobs/{id}/run` | Run immediately |
| `DELETE` | `/api/jobs/{id}` | Delete job |
| `GET` | `/api/jobs/{id}/runs` | Run history |
| `GET` | `/health` | Health check |

### Example

```bash
curl -X POST http://127.0.0.1:8000/api/search/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"auto","domain":"Salon","location":"Delhi","max_results":10}'
```

---

## Project structure

```
leadgen/
├── app/
│   ├── main.py               # FastAPI app, all endpoints
│   ├── scheduler_service.py  # APScheduler: exact-time cron/interval triggers
│   ├── router_engine.py      # auto vs custom source dispatch
│   ├── crud.py               # upsert + dedup + new-lead marking
│   ├── models.py             # Lead, ScheduledJob, JobRunLog
│   ├── schemas.py            # Pydantic request/response models
│   ├── enricher.py           # website check + digital presence score
│   ├── database.py           # SQLite engine + lightweight migrations
│   └── scrapers/             # gmaps · linkedin · facebook · instagram
├── templates/                # Jinja2: base.html, index.html
├── static/                   # style.css, alpine.js (fully offline)
├── data/                     # SQLite DB + CSV exports (git-ignored)
├── requirements.txt
├── start_multi.bat           # Windows one-click launcher
└── run.py
```

---

## Tech stack

**Python 3.11 · FastAPI · Uvicorn · SQLAlchemy + SQLite · APScheduler · Playwright + BeautifulSoup4 (scraper hooks) · Jinja2 · Alpine.js (self-hosted)**

---

## License

MIT — free to use, modify and ship.
