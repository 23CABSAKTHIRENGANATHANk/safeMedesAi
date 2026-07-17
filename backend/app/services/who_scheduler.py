"""Scheduler for WHO scraper to run daily."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from .who_service import ingest_who_listing

log = logging.getLogger('service.who.scheduler')
_scheduler = None

def start_who_scheduler():
    global _scheduler
    if _scheduler:
        return _scheduler
    sched = BackgroundScheduler()
    sched.add_job(lambda: ingest_who_listing(), 'interval', days=1, id='who_daily')
    sched.start()
    _scheduler = sched
    log.info('WHO scheduler started - running daily')
    return sched

def shutdown_who_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        log.info('WHO scheduler shut down')
