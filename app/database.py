"""Database engine and session management (sync)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _migrate(conn, table, columns):
    # columns: list of (name, sql_type)
    existing = {r[1] for r in conn.execute(__import__("sqlalchemy").text(f"PRAGMA table_info({table})")).fetchall()}
    for name, typ in columns:
        if name not in existing:
            conn.execute(__import__("sqlalchemy").text(f"ALTER TABLE {table} ADD COLUMN {name} {typ}"))
            conn.commit()


def init_db():
    from . import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    # lightweight migration for newly added columns
    import sqlalchemy
    with engine.connect() as conn:
        _migrate(conn, "scheduled_jobs", [("run_time", "VARCHAR(10)"), ("run_days", "VARCHAR(50)")])
        conn.commit()