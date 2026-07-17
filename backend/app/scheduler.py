"""Application scheduler bridge.

This module integrates the centralized job runner (`app.jobs.job_runner`) with
the FastAPI application lifecycle. It ensures scheduled jobs are started once
and shut down gracefully.
"""
import logging
from typing import Optional

from .jobs.job_runner import start_all_jobs, shutdown_all_jobs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler")

_started = False


def start_scheduler():
    global _started
    if _started:
        logger.info('Scheduler already started; skipping')
        return
    try:
        start_all_jobs()
        _started = True
        logger.info('Background scheduler started successfully via job_runner')
    except Exception:
        logger.exception('Failed to start job_runner scheduler')


def stop_scheduler():
    global _started
    if not _started:
        logger.info('Scheduler not running; nothing to stop')
        return
    try:
        shutdown_all_jobs()
        _started = False
        logger.info('Background scheduler shut down via job_runner')
    except Exception:
        logger.exception('Failed to shutdown job_runner scheduler')
