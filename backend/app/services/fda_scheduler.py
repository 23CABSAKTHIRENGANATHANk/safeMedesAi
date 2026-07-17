"""Scheduler to refresh OpenFDA data periodically."""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from .fda_service import refresh_all_to_supabase

log = logging.getLogger('service.fda.scheduler')

_scheduler = None

def start_fda_scheduler():
    global _scheduler
    if _scheduler:
        return _scheduler
    sched = BackgroundScheduler()
    # run every 6 hours
    sched.add_job(lambda: refresh_all_to_supabase(limit=100, pages=1), 'interval', hours=6, id='openfda_refresh')
    sched.start()
    _scheduler = sched
    log.info('OpenFDA scheduler started - running every 6 hours')
    return sched

def shutdown_fda_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        log.info('OpenFDA scheduler shut down')
