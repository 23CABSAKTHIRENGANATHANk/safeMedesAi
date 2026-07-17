"""CDSCO Scraper

This is a production-ready scraper skeleton to collect:
 - Approved Medicines
 - Drug Alerts
 - NSQ Drugs
 - Recall Notifications

It downloads PDFs, extracts tables (pdfplumber), cleans data, and upserts into Supabase.

Configure environment with a .env file (see .env.example).
"""
import os
import logging
import requests
from bs4 import BeautifulSoup
import pdfplumber
import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv
from db import get_client, upsert_manufacturer, upsert_medicine, insert_alert, insert_recall
from utils import ensure_dir, sanitize_filename

load_dotenv()
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(level=LOG_LEVEL)
log = logging.getLogger('cdsco.scraper')

DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', './data/pdfs')
ensure_dir(DOWNLOAD_DIR)

HEADERS = {
    'User-Agent': 'MedVerify Scraper (+https://example.org)'
}

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=30))
def fetch_url(url: str, stream=False, timeout=30):
    log.debug('Fetching URL %s', url)
    r = requests.get(url, headers=HEADERS, timeout=timeout, stream=stream)
    r.raise_for_status()
    return r

def download_pdf(url: str) -> str:
    resp = fetch_url(url, stream=True)
    fname = sanitize_filename(url)
    path = os.path.join(DOWNLOAD_DIR, fname)
    with open(path, 'wb') as f:
        for chunk in resp.iter_content(1024 * 32):
            if chunk:
                f.write(chunk)
    log.info('Saved PDF %s', path)
    return path

def extract_tables_from_pdf(path: str):
    tables = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                try:
                    tbl = page.extract_table()
                    if tbl and len(tbl) > 1:
                        df = pd.DataFrame(tbl[1:], columns=tbl[0])
                        tables.append(df)
                except Exception:
                    log.exception('Failed to extract table on page')
    except Exception:
        log.exception('Failed to open PDF %s', path)
    return tables

def clean_medicine_row(row: dict) -> dict:
    # basic cleaning: strip whitespace, normalize case
    out = {}
    for k, v in row.items():
        if isinstance(v, str):
            out[k.strip().lower()] = ' '.join(v.split())
        else:
            out[k.strip().lower()] = v
    return out

class CDSCOScraper:
    def __init__(self, supabase_client=None):
        self.client = supabase_client or get_client()

    def parse_listing_page(self, url: str):
        r = fetch_url(url)
        soup = BeautifulSoup(r.text, 'html.parser')
        # Placeholder: find links to PDFs or detail pages
        links = []
        for a in soup.select('a'):
            href = a.get('href')
            if href and href.lower().endswith('.pdf'):
                links.append(requests.compat.urljoin(url, href))
        return links

    def ingest_pdf_resource(self, pdf_url: str, kind: str):
        try:
            path = download_pdf(pdf_url)
            tables = extract_tables_from_pdf(path)
            # Basic processing: for each table, make DataFrame and ingest rows
            for df in tables:
                records = df.fillna('').to_dict(orient='records')
                for r in records:
                    cleaned = clean_medicine_row(r)
                    # map cleaned to schema (best-effort)
                    medicine = {
                        'name': cleaned.get('name') or cleaned.get('medicine') or cleaned.get('drug') or 'unknown',
                        'form': cleaned.get('form'),
                        'strength': cleaned.get('strength'),
                        'primary_identifier': cleaned.get('ndc') or cleaned.get('barcode') or None,
                        'metadata': {'source_pdf': os.path.basename(path), 'raw': r}
                    }
                    try:
                        upsert_medicine(self.client, medicine)
                    except Exception:
                        log.exception('Failed upsert medicine')
            return True
        except Exception:
            log.exception('Failed to ingest pdf %s', pdf_url)
            return False

    def run(self):
        # Example seed URLs — replace with authoritative CDSCO endpoints
        pages = {
            'approved': 'https://cdsco.gov.in/approved-medicines.html',
            'alerts': 'https://cdsco.gov.in/drug-alerts.html',
        }
        for kind, url in pages.items():
            try:
                pdfs = self.parse_listing_page(url)
                for p in pdfs:
                    self.ingest_pdf_resource(p, kind)
            except Exception:
                log.exception('Failed processing %s', url)

if __name__ == '__main__':
    client = get_client()
    scraper = CDSCOScraper(client)
    scraper.run()
