"""FastAPI router to expose scraper controls."""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from .scraper_service import ScraperService
from .scheduler import start_scheduler
import logging

log = logging.getLogger('scraper.api')

router = APIRouter(prefix='/scrapers', tags=['scrapers'])
svc = ScraperService()


@router.post('/run')
def run_scrape(background: BackgroundTasks):
    """Trigger a background scrape run immediately."""
    background.add_task(svc.run_all_once)
    return {'status': 'scheduled'}


@router.get('/status')
def status():
    return {'last_run': svc.last_run.isoformat() if svc.last_run else None}


@router.post('/start-scheduler')
def start():
    try:
        start_scheduler()
        return {'status': 'scheduler_started'}
    except Exception as e:
        log.exception('start scheduler failed')
        raise HTTPException(status_code=500, detail=str(e))
