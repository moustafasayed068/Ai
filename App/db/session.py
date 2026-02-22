# App/db/session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from App.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Validate configuration
if settings.DB_MODE in ["supabase", "both"] and not settings.SUPABASE_DB_URL:
    raise ValueError(
        f"DB_MODE is '{settings.DB_MODE}' but SUPABASE_DB_URL is not configured"
    )

# Local DB Engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Supabase DB Engine
supabase_engine = None
SupabaseSession = None

if settings.DB_MODE in ["supabase", "both"]:
    try:
        supabase_engine = create_engine(
            settings.SUPABASE_DB_URL,
            pool_pre_ping=True,
        )
        SupabaseSession = sessionmaker(
            autocommit=False, autoflush=False, bind=supabase_engine
        )
        logger.info(f"Supabase initialized (mode: {settings.DB_MODE})")
    except Exception as e:
        logger.error(f"Supabase init failed: {e}")
        if settings.DB_MODE == "supabase":
            raise
        logger.warning("Continuing with local DB only")

# Dependency functions

def get_db():
    if settings.DB_MODE == "supabase":
        if SupabaseSession is None:
            raise ValueError("Supabase not configured")
        db = SupabaseSession()
    else:
        db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_local_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_supabase_db():
    if SupabaseSession is None:
        raise ValueError("Supabase not configured")

    db = SupabaseSession()
    try:
        yield db
    finally:
        db.close()
