import os
import logging
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv


FALLBACK_MEDICINES = [
    {
        "name": "Paracetamol",
        "batch": "SAFE-001",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Dolo 650",
        "batch": "SAFE-002",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Crocin",
        "batch": "SAFE-003",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Amoxicillin",
        "batch": "WARN-001",
        "manufacturer": "Generic",
        "status": "warning",
        "authority": "WHO GSMS",
        "reason": "A counterfeit or falsified version of this medicine was detected in the fallback dataset.",
    },
    {
        "name": "Ibuprofen",
        "batch": "SAFE-004",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Aspirin",
        "batch": "SAFE-005",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Metformin",
        "batch": "SAFE-006",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Ciprofloxacin",
        "batch": "SAFE-007",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Pantoprazole",
        "batch": "SAFE-008",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Cetirizine",
        "batch": "SAFE-009",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Atorvastatin",
        "batch": "SAFE-010",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Azithromycin",
        "batch": "SAFE-011",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Omeprazole",
        "batch": "SAFE-012",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Amlodipine",
        "batch": "SAFE-013",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Metoprolol",
        "batch": "SAFE-014",
        "manufacturer": "Generic",
        "status": "safe",
        "authority": "Local Fallback",
        "reason": "No active recall or alert matched this medicine in the fallback dataset.",
    },
    {
        "name": "Vioxx",
        "batch": "UNSAFE-001",
        "manufacturer": "Merck",
        "status": "unsafe",
        "authority": "US FDA",
        "reason": "This medicine has a documented safety recall in the fallback dataset.",
    },
    {
        "name": "Rofecoxib",
        "batch": "UNSAFE-002",
        "manufacturer": "Merck",
        "status": "unsafe",
        "authority": "US FDA",
        "reason": "This medicine has a documented safety recall in the fallback dataset.",
    },
    {
        "name": "Sibutramine",
        "batch": "UNSAFE-003",
        "manufacturer": "Generic",
        "status": "unsafe",
        "authority": "WHO GSMS",
        "reason": "This medicine has a documented safety recall in the fallback dataset.",
    },
    {
        "name": "Avandia",
        "batch": "UNSAFE-004",
        "manufacturer": "GSK",
        "status": "unsafe",
        "authority": "US FDA",
        "reason": "This medicine has a documented safety recall in the fallback dataset.",
    },
    {
        "name": "Cisapride",
        "batch": "UNSAFE-005",
        "manufacturer": "Generic",
        "status": "unsafe",
        "authority": "US FDA",
        "reason": "This medicine has a documented safety recall in the fallback dataset.",
    },
    {
        "name": "Thalidomide",
        "batch": "UNSAFE-006",
        "manufacturer": "Generic",
        "status": "unsafe",
        "authority": "CDSCO",
        "reason": "This medicine has a documented safety recall in the fallback dataset.",
    },
]

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
try:
    if DATABASE_URL.startswith("sqlite:"):
        engine = create_engine(
            DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=False,
        )
    else:
        # Create engine without immediate connection test
        engine = create_engine(
            DATABASE_URL,
            # Connection pool settings optimized for Supabase (serverless-friendly)
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,       # Verify connections are alive before use
            pool_recycle=300,         # Recycle connections every 5 minutes to avoid timeouts
            echo=False,               # Set to True for SQL query debugging
            connect_args={"connect_timeout": 10},
        )
        
        # Try to connect with timeout, but don't block startup
        try:
            logger.info("Testing connection to PostgreSQL database...")
            with engine.connect() as conn:
                logger.info("✓ Successfully connected to PostgreSQL database")
        except Exception as db_error:
            logger.warning("⚠ Failed to connect to PostgreSQL at %s: %s", DATABASE_URL, str(db_error))
            logger.warning("Falling back to local SQLite database for this session")
            DATABASE_URL = "sqlite:///./dev.db"
            engine = create_engine(
                DATABASE_URL,
                connect_args={"check_same_thread": False},
                echo=False,
            )
except Exception as e:
    logger.error("Fatal error creating database engine: %s", str(e))
    logger.error("Falling back to SQLite")
    DATABASE_URL = "sqlite:///./dev.db"
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def seed_local_fallback_data(session):
    from .models.medicine import MedicineRecord

    seeded = 0
    for item in FALLBACK_MEDICINES:
        existing = session.query(MedicineRecord).filter(
            MedicineRecord.name.ilike(item["name"])
        ).first()
        if existing:
            continue

        session.add(
            MedicineRecord(
                name=item["name"],
                batch=item.get("batch"),
                manufacturer=item.get("manufacturer"),
                status=item["status"],
                authority=item["authority"],
                reason=item["reason"],
            )
        )
        seeded += 1

    session.commit()
    logger.info("Seeded %s fallback medicine records into the local database", seeded)
    return seeded


def get_db():
    """Dependency injection for FastAPI route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
