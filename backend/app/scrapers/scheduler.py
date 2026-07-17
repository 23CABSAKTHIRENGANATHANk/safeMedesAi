"""Scheduler to run ScraperService periodically using APScheduler."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from .scraper_service import ScraperService
from datetime import timedelta

log = logging.getLogger('scraper.scheduler')

_scheduler = None

def start_scheduler():
    global _scheduler
    if _scheduler:
        return _scheduler
    svc = ScraperService()
    sched = BackgroundScheduler()
    # run every 24 hours
    sched.add_job(svc.run_all_once, 'interval', hours=24, id='cdsco_daily')
    sched.start()
    _scheduler = sched
    log.info('Scraper scheduler started - running every 24 hours')
    return sched

def shutdown_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        log.info('Scraper scheduler shut down')
