"""Page-specific parsers for CDSCO resources."""
from typing import List, Dict
import logging
import requests
from bs4 import BeautifulSoup
from .http import fetch
from .pdf_utils import download_pdf, extract_tables
from .supabase_client import get_client, upsert_medicine, insert_alert, insert_recall

log = logging.getLogger('scraper.parsers')


def find_pdf_links_from_listing(url: str) -> List[str]:
    """Fetch a listing page and return absolute PDF links found on it.

    Handles direct .pdf links, CDSCO download endpoints, and follows listing pages
    to find PDF links on linked pages if needed.
    """
    r = fetch(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    links: List[str] = []
    page_candidates: List[str] = []

    for a in soup.select('a'):
        href = a.get('href')
        if not href:
            continue
        full_url = requests.compat.urljoin(url, href)
        lh = href.lower()
        if '.pdf' in lh or 'pdf-documents' in lh or 'download_file_division.jsp' in lh:
            links.append(full_url)
        elif href.startswith('/') or 'cdsco.gov.in' in href.lower():
            page_candidates.append(full_url)

    # fallback: if no direct PDF links were found, inspect linked pages for PDFs
    if not links and page_candidates:
        page_candidates = page_candidates[:50]
        for page_url in page_candidates:
            try:
                page_resp = fetch(page_url)
            except Exception:
                continue
            page_soup = BeautifulSoup(page_resp.text, 'html.parser')
            for a in page_soup.select('a'):
                href = a.get('href')
                if not href:
                    continue
                lh = href.lower()
                if '.pdf' in lh or 'pdf-documents' in lh or 'download_file_division.jsp' in lh:
                    links.append(requests.compat.urljoin(page_url, href))
            if links:
                break

    logging.getLogger('scraper.parsers').info('Found %d candidate pdf links on %s', len(links), url)
    return links


def normalize_row(row: Dict[str, str]) -> Dict[str, str]:
    """Normalize a parsed table row: trim, lower keys, and coalesce common column names."""
    out: Dict[str, str] = {}
    for k, v in row.items():
        if k is None:
            continue
        key = k.strip().lower()
        val = v.strip() if isinstance(v, str) else v
        out[key] = val

    # map common synonyms
    mapped = {
        'name': out.get('name') or out.get('medicine') or out.get('drug') or out.get('product name'),
        'form': out.get('form') or out.get('dosage form') or out.get('dosage'),
        'strength': out.get('strength') or out.get('dose') or out.get('dosage strength'),
        'batch': out.get('batch no') or out.get('batch') or out.get('lot no') or out.get('lot'),
        'regno': out.get('reg no') or out.get('regn') or out.get('regn no') or out.get('regno') or out.get('registration no'),
    }
    mapped = {k: (v if v is not None else '') for k, v in mapped.items()}
    return mapped


def ingest_approved_medicines(url: str, dest_dir: str):
    client = get_client()
    links = find_pdf_links_from_listing(url)
    for pdf in links:
        path = download_pdf(pdf, dest_dir)
        tables = extract_tables(path)
        for df in tables:
            for row in df.fillna('').to_dict(orient='records'):
                normalized = normalize_row(row)
                name = normalized.get('name')
                if not name:
                    logging.getLogger('scraper.parsers').warning('Skipping row without name in %s', path)
                    continue
                med = {
                    'name': name,
                    'form': normalized.get('form') or None,
                    'strength': normalized.get('strength') or None,
                    'batch': normalized.get('batch') or None,
                    'primary_identifier': normalized.get('regno') or None,
                    'metadata': {'source_pdf': path}
                }
                upsert_medicine(client, med)


def ingest_drug_alerts(url: str, dest_dir: str):
    client = get_client()
    links = find_pdf_links_from_listing(url)
    for pdf in links:
        path = download_pdf(pdf, dest_dir)
        tables = extract_tables(path)
        for df in tables:
            for row in df.fillna('').to_dict(orient='records'):
                normalized = normalize_row(row)
                title = normalized.get('name') or normalized.get('regno') or 'Drug Alert'
                alert = {
                    'title': title,
                    'severity': None,
                    'description': str(row),
                    'source_url': pdf,
                    'metadata': {'source_pdf': path}
                }
                insert_alert(client, alert)


def ingest_recalls(url: str, dest_dir: str):
    client = get_client()
    links = find_pdf_links_from_listing(url)
    for pdf in links:
        path = download_pdf(pdf, dest_dir)
        tables = extract_tables(path)
        for df in tables:
            for row in df.fillna('').to_dict(orient='records'):
                normalized = normalize_row(row)
                title = normalized.get('name') or 'Recall'
                recall = {
                    'title': title,
                    'reason': None,
                    'affected_medicine': normalized.get('name') or '',
                    'source_url': pdf,
                    'metadata': {'source_pdf': path}
                }
                insert_recall(client, recall)


def ingest_nsq(url: str, dest_dir: str):
    """Ingest NSQ (Not of Standard Quality) lists."""
    client = get_client()
    links = find_pdf_links_from_listing(url)
    for pdf in links:
        path = download_pdf(pdf, dest_dir)
        tables = extract_tables(path)
        for df in tables:
            for row in df.fillna('').to_dict(orient='records'):
                normalized = normalize_row(row)
                name = normalized.get('name')
                if not name:
                    logging.getLogger('scraper.parsers').warning('Skipping NSQ row without name in %s', path)
                    continue
                med = {
                    'name': name,
                    'form': normalized.get('form') or None,
                    'strength': normalized.get('strength') or None,
                    'batch': normalized.get('batch') or None,
                    'primary_identifier': None,
                    'metadata': {'nsq': True, 'source_pdf': path}
                }
                upsert_medicine(client, med)
