"""WHO Medical Product Alerts scraper service.

Collects Medical Product Alerts, Counterfeit Medicine Alerts, and Substandard
Medicine notifications from WHO website. Downloads PDFs when present,
extracts tables with pdfplumber, normalizes data and upserts into Supabase.
"""
from typing import List, Dict
import logging
import os
from bs4 import BeautifulSoup
from .fda_service import fetch_openfda  # reuse fetch pattern for retries
import requests
from ..scrapers.pdf_utils import download_pdf, extract_tables
from ..scrapers.supabase_client import get_client, upsert_who_alert

log = logging.getLogger('service.who')

WHO_ALERTS_URL = os.getenv('WHO_ALERTS_URL', 'https://www.who.int/medical-product-alerts')
DOWNLOAD_DIR = os.getenv('WHO_DOWNLOAD_DIR', '/tmp/who_pdfs')


def fetch_page(url: str) -> str:
    log.debug('Fetching WHO page %s', url)
    r = requests.get(url, timeout=30, headers={'User-Agent': 'MedVerify/WHO-Scraper'})
    r.raise_for_status()
    return r.text


def find_alert_links(html: str, base: str) -> List[str]:
    soup = BeautifulSoup(html, 'html.parser')
    links: List[str] = []
    for a in soup.select('a'):
        href = a.get('href')
        if not href:
            continue
        lh = href.lower()
        # WHO uses /news/item/ or /medical-product-alerts/ and often links to PDFs under /../PDFs/
        if 'medical-product-alert' in lh or lh.endswith('.pdf') or 'pdf' in lh or '/news/item/' in lh:
            links.append(requests.compat.urljoin(base, href))
    log.info('WHO: found %d candidate links', len(links))
    return links


def normalize_alert_row(row: Dict[str, str]) -> Dict[str, str]:
    # Simple normalization: keep title, description, date, affected product
    title = row.get('title') or row.get('name') or row.get('alert')
    affected = row.get('product') or row.get('product name') or row.get('affected product')
    date = row.get('date') or row.get('issued')
    return {
        'external_id': row.get('id') or None,
        'title': title or 'WHO Medical Product Alert',
        'summary': row.get('summary') or None,
        'affected_product': affected or None,
        'date': date or None,
        'source': 'who',
        'metadata': {'raw': row}
    }


def ingest_who_listing(url: str = None):
    url = url or WHO_ALERTS_URL
    html = fetch_page(url)
    links = find_alert_links(html, url)
    client = get_client()
    ingested = 0
    for link in links:
        try:
            if link.lower().endswith('.pdf'):
                path = download_pdf(link, DOWNLOAD_DIR)
                tables = extract_tables(path)
                for df in tables:
                    for row in df.fillna('').to_dict(orient='records'):
                        normalized = normalize_alert_row({k.lower().strip(): (v or '') for k, v in row.items()})
                        upsert_who_alert(client, normalized)
                        ingested += 1
            else:
                # attempt to fetch page and extract content text as a single record
                page_html = fetch_page(link)
                soup = BeautifulSoup(page_html, 'html.parser')
                title = (soup.find('h1') or soup.find('h2') or soup.title).get_text(strip=True) if soup.find('h1') or soup.find('h2') or soup.title else 'WHO Alert'
                paragraphs = ' '.join(p.get_text(strip=True) for p in soup.find_all('p')[:5])
                rec = {'title': title, 'summary': paragraphs, 'affected_product': None, 'date': None, 'external_id': None, 'source': 'who', 'metadata': {'source_url': link}}
                upsert_who_alert(client, rec)
                ingested += 1
        except Exception:
            log.exception('Failed to ingest WHO link %s', link)
    log.info('WHO ingestion complete, ingested %d items', ingested)
    return ingested
