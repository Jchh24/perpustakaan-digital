import os
import sys
import logging
import urllib.parse
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

logger = logging.getLogger("perpustakaan_digital.db")

raw_db_url = os.getenv("DATABASE_URL", "postgresql://postgres:admin@localhost:5432/perpustakaan_digital")

if raw_db_url.startswith("postgresql://"):
    DATABASE_URL = raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
else:
    DATABASE_URL = raw_db_url

def ensure_postgres_db(url: str):
    try:
        clean_url = url.replace("postgresql+psycopg2://", "postgresql://")
        parsed = urllib.parse.urlparse(clean_url)
        target_db = parsed.path.lstrip("/")
        if not target_db:
            return
        maint_parsed = parsed._replace(path="/postgres")
        maint_url = urllib.parse.urlunparse(maint_parsed)
        conn = psycopg2.connect(maint_url, connect_timeout=3)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (target_db,))
        exists = cur.fetchone()
        if not exists:
            cur.execute(f'CREATE DATABASE "{target_db}"')
        cur.close()
        conn.close()
    except Exception:
        pass

try:
    if "postgresql" in DATABASE_URL:
        ensure_postgres_db(DATABASE_URL)
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 3})
        with engine.connect() as conn:
            pass
        print(f"[DATABASE] Connected to PostgreSQL via psycopg2: {DATABASE_URL.split('@')[-1]}")
    else:
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        print(f"[DATABASE] Connected to SQLite: {DATABASE_URL}")
except Exception as e:
    print(f"[DATABASE ERROR] Gagal terhubung ke PostgreSQL via psycopg2: {e}", file=sys.stderr)
    FALLBACK_URL = "sqlite:///./data/perpustakaan.db"
    print(f"[DATABASE WARNING] Mengalihkan koneksi sementara ke SQLite: {FALLBACK_URL}", file=sys.stderr)
    DATABASE_URL = FALLBACK_URL
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_psycopg2_connection():
    clean_url = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://")
    if clean_url.startswith("postgresql://"):
        return psycopg2.connect(clean_url)
    return None

def init_db():
    os.makedirs("./data", exist_ok=True)
    from app.models.user import User
    from app.models.category import Category
    from app.models.book import Book
    from app.models.loan import Loan
    Base.metadata.create_all(bind=engine)
