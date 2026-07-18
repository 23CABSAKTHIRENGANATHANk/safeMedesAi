import os
import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base, SessionLocal, seed_local_fallback_data
from .scheduler import start_scheduler, stop_scheduler
from .api.verify import router as verify_router
from .api.medicines import router as medicines_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Create tables in the database on application startup if they don't exist
Base.metadata.create_all(bind=engine)

with SessionLocal() as session:
    seed_local_fallback_data(session)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    logger.info("Starting up FastAPI application...")
    start_scheduler()
    yield
    # Shutdown actions
    logger.info("Shutting down FastAPI application...")
    stop_scheduler()

app = FastAPI(
    title="SafeMeds AI Backend",
    description="Regulatory-grade medicine verification API service",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Origins
cors_origins_raw = os.getenv(
    "CORS_ORIGINS",
    '["http://localhost:5173","http://127.0.0.1:5173","http://localhost:5174","http://127.0.0.1:5174","http://localhost:5175","http://127.0.0.1:5175"]'
)
try:
    origins = json.loads(cors_origins_raw)
except Exception:
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "https://safe-medes-ai.vercel.app",
        "https://safe-meds-ai.vercel.app",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(verify_router, prefix="/api", tags=["Verification"])
app.include_router(medicines_router)

@app.get("/")
def read_root():
    return {
        "status": "healthy",
        "service": "SafeMeds AI Backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("main:app", host=host, port=port, reload=True)
