"""Central job runner for scheduled scraper tasks.

Schedules and runs:
- OpenFDA refresh every 6 hours
- CDSCO scrape every 24 hours
- WHO ingest every 24 hours

Each job is retried on failure (Tenacity) and every execution is logged to
`backend/logs/scraper_jobs.log` with start/end/time and status.
"""
import os
import json
import logging
from datetime import datetime
from typing import Callable
from apscheduler.schedulers.background import BackgroundScheduler
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..services.fda_service import refresh_all_to_supabase
from ..scrapers.scraper_service import ScraperService
from ..services.who_service import ingest_who_listing

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '..', 'logs')
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'logs'))
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'scraper_jobs.log')

logger = logging.getLogger('jobs.runner')
logger.setLevel(logging.INFO)
fh = logging.FileHandler(LOG_FILE)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)


def _log_execution(name: str, start: datetime, end: datetime, status: str, details: str = ''):
    entry = {
        'job': name,
        'start': start.isoformat(),
        'end': end.isoformat(),
        'duration_seconds': (end - start).total_seconds(),
        'status': status,
        'details': details
    }
    # append JSON line
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    logger.info('Job %s finished status=%s duration=%.2f', name, status, entry['duration_seconds'])


def _safe_run(name: str, func: Callable[[], int]):
    start = datetime.utcnow()
    try:
        logger.info('Job %s started', name)
        count = func()
        end = datetime.utcnow()
        _log_execution(name, start, end, 'success', f'ingested={count}')
    except Exception as e:
        end = datetime.utcnow()
        logger.exception('Job %s failed', name)
        _log_execution(name, start, end, 'failed', str(e))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=5, max=60), retry=retry_if_exception_type(Exception))
def run_fda_once() -> int:
    # pages and limit controlled via env if needed
    return refresh_all_to_supabase(limit=100, pages=1)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=5, max=60), retry=retry_if_exception_type(Exception))
def run_cdsco_once() -> int:
    svc = ScraperService()
    ok = svc.run_all_once()
    return 1 if ok else 0


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=5, max=60), retry=retry_if_exception_type(Exception))
def run_who_once() -> int:
    return ingest_who_listing()


_scheduler = None


def start_all_jobs():
    global _scheduler
    if _scheduler:
        return _scheduler
    sched = BackgroundScheduler()
    # FDA every 6 hours
    sched.add_job(lambda: _safe_run('openfda_refresh', run_fda_once), 'interval', hours=6, id='openfda_refresh', max_instances=1)
    # CDSCO daily
    sched.add_job(lambda: _safe_run('cdsco_daily', run_cdsco_once), 'interval', hours=24, id='cdsco_daily', max_instances=1)
    # WHO daily
    sched.add_job(lambda: _safe_run('who_daily', run_who_once), 'interval', days=1, id='who_daily', max_instances=1)
    sched.start()
    _scheduler = sched
    logger.info('All scheduled jobs started: FDA(6h), CDSCO(24h), WHO(24h)')
    return sched


def shutdown_all_jobs():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info('All scheduled jobs shut down')


if __name__ == '__main__':
    # allow running standalone for debugging
    start_all_jobs()
    import time
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        shutdown_all_jobs()
