import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("database")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback to a local sqlite DB for development and verification when DATABASE_URL
    # is not provided. This allows the FastAPI app to start and run without Supabase
    # credentials. For production, set DATABASE_URL to your Supabase Postgres URL.
    logger.warning("DATABASE_URL not set. Falling back to local sqlite database './dev.db' for development.")
    DATABASE_URL = "sqlite:///./dev.db"

# Ensure correct SQLAlchemy driver prefix for psycopg2
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Use different engine options for sqlite vs postgres
if DATABASE_URL.startswith("sqlite:"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        # Connection pool settings optimized for Supabase (serverless-friendly)
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,       # Verify connections are alive before use
        pool_recycle=300,         # Recycle connections every 5 minutes to avoid timeouts
        echo=False,               # Set to True for SQL query debugging
    )

# If a remote database is configured but unreachable, fall back to sqlite for
# local development so the service can start. This avoids hard crashes when
# network/DNS resolution fails during initial startup.
if not DATABASE_URL.startswith("sqlite:"):
    try:
        # Quick connectivity check
        with engine.connect() as conn:
            pass
    except Exception:
        logger.exception("Failed to connect to database at %s — falling back to sqlite './dev.db'", DATABASE_URL)
        DATABASE_URL = "sqlite:///./dev.db"
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=False,
        )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency injection for FastAPI route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
