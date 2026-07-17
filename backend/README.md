# Backend scrapers

This folder contains CDSCO scraper services used by the FastAPI backend.

Setup
- Copy environment variables into a `.env` file at the project root or the backend folder:

```
SUPABASE_URL=https://xyz.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci... (keep secret)
CDSCO_APPROVED_URL=https://cdsco.gov.in/approved-medicines.html
CDSCO_ALERTS_URL=https://cdsco.gov.in/drug-alerts.html
CDSCO_RECALLS_URL=https://cdsco.gov.in/recalls.html
CDSCO_NSQ_URL=https://cdsco.gov.in/nsq-drugs.html
SCRAPER_DOWNLOAD_DIR=./data/pdfs
```

Install dependencies (recommended in venv):

```bash
python -m pip install -r backend/requirements.txt
```

Run once (manual):

```bash
python -c "from app.scrapers.scraper_service import ScraperService; ScraperService().run_all_once()"
```

Start scheduler from FastAPI app (example integration):

```py
from fastapi import FastAPI
from app.scrapers.api import router

app = FastAPI()
app.include_router(router)

# Optionally start scheduler at startup
@app.on_event('startup')
def startup():
    from app.scrapers.scheduler import start_scheduler
    start_scheduler()
```
