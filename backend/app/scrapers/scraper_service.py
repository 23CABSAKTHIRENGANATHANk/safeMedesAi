"""High-level ScraperService to run CDSCO ingest jobs and track status."""
import os
import logging
from datetime import datetime
from .cdsco_parsers import ingest_approved_medicines, ingest_drug_alerts, ingest_recalls, ingest_nsq

log = logging.getLogger('scraper.service')

DEFAULT_DEST = os.getenv('SCRAPER_DOWNLOAD_DIR', '/tmp/scraper_pdfs')

class ScraperService:
    def __init__(self, dest_dir: str = None):
        self.dest_dir = dest_dir or DEFAULT_DEST
        self.last_run = None

    def run_all_once(self):
        """Run all configured CDSCO ingestion jobs once."""
        log.info('Starting full CDSCO scrape')
        try:
            # URLs are configurable via env vars; fallbacks are placeholders
            approved_url = os.getenv('CDSCO_APPROVED_URL', 'https://cdsco.gov.in/approved-medicines.html')
            alerts_url = os.getenv('CDSCO_ALERTS_URL', 'https://cdsco.gov.in/drug-alerts.html')
            recalls_url = os.getenv('CDSCO_RECALLS_URL', 'https://cdsco.gov.in/recalls.html')
            nsq_url = os.getenv('CDSCO_NSQ_URL', 'https://cdsco.gov.in/nsq-drugs.html')

            ingest_approved_medicines(approved_url, self.dest_dir)
            ingest_nsq(nsq_url, self.dest_dir)
            ingest_drug_alerts(alerts_url, self.dest_dir)
            ingest_recalls(recalls_url, self.dest_dir)

            self.last_run = datetime.utcnow()
            log.info('CDSCO scrape completed at %s', self.last_run.isoformat())
            return True
        except Exception:
            log.exception('Full scrape failed')
            return False
