"""Full ETL import runner -- runs all sources and verifies Supabase table counts.

Usage (from project root):
    .venv\\Scripts\\python backend\\scripts\\run_import.py

Sources:
  1. OpenFDA drug labels  -> medicines (linked to manufacturers)
  2. OpenFDA enforcement  -> drug_recalls
  3. CDSCO Latest Alerts  -> drug_alerts (via downloaded PDFs)
  4. WHO Medical Product Alerts -> drug_alerts

After import, prints record count for each of the target tables.
"""
import os
import sys
import logging
import time

# -- 0. Bootstrap paths & env --------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
REPO_ROOT   = os.path.dirname(BACKEND_DIR)

# Load root .env first
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(REPO_ROOT, '.env'), override=False)
# Then backend .env
load_dotenv(dotenv_path=os.path.join(BACKEND_DIR, '.env'), override=True)

# Add both root and backend to sys.path so package imports resolve
for p in [REPO_ROOT, BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

# -- 1. Logging setup ----------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s -- %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger('run_import')

# -- 2. Check env vars ---------------------------------------------------------
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    log.error('Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY -- cannot continue')
    sys.exit(1)

# -- 3. Supabase client and imports --------------------------------------------
from backend.app.scrapers.supabase_client import (
    get_client,
    upsert_medicine,
    insert_alert,
    insert_recall,
    upsert_recall,
    upsert_who_alert,
    upsert_report
)

client = get_client()
log.info('Supabase client created OK')

def count_table(tbl):
    try:
        res = client.table(tbl).select('*', count='exact').execute()
        if hasattr(res, 'count') and res.count is not None:
            return res.count
        return len(res.data or [])
    except Exception as e:
        log.warning('count %s failed: %s', tbl, e)
        return -1

# -- 4. Phase 1: OpenFDA labels -> medicines -----------------------------------
def run_openfda_labels(limit=100, pages=2):
    log.info('=== Phase 1: OpenFDA drug labels -> medicines ===')
    import requests
    total = 0
    OPENFDA_BASE = os.getenv('OPENFDA_BASE', 'https://api.fda.gov')
    for page in range(pages):
        skip = page * limit
        try:
            r = requests.get(
                f'{OPENFDA_BASE}/drug/label.json',
                params={'limit': limit, 'skip': skip},
                timeout=30,
                headers={'User-Agent': 'MedVerify/Import'}
            )
            r.raise_for_status()
            results = r.json().get('results', [])
            log.info('  Page %d: %d label records from OpenFDA', page + 1, len(results))
            for item in results:
                try:
                    openfda = item.get('openfda', {})
                    names = openfda.get('generic_name') or openfda.get('brand_name') or []
                    name = (names[0] if isinstance(names, list) and names else str(names)) if names else None
                    if not name:
                        continue
                    mfr_list = openfda.get('manufacturer_name') or []
                    manufacturer = mfr_list[0] if isinstance(mfr_list, list) and mfr_list else None
                    med = {
                        'name': str(name)[:500],
                        'form': None,
                        'strength': None,
                        'manufacturer': manufacturer,
                        'primary_identifier': item.get('id'),
                        'metadata': {'source': 'openfda_label', 'id': item.get('id')}
                    }
                    upsert_medicine(client, med)
                    total += 1
                except Exception as e:
                    log.debug('  label item upsert failed: %s', e)
        except Exception as e:
            log.warning('  OpenFDA labels page %d failed: %s', page + 1, e)
        time.sleep(0.5)
    log.info('Phase 1 done: %d medicines upserted', total)
    return total

# -- 5. Phase 2: OpenFDA enforcement -> drug_recalls ---------------------------
def run_openfda_recalls(limit=100, pages=1):
    log.info('=== Phase 2: OpenFDA enforcement -> drug_recalls ===')
    import requests
    total = 0
    OPENFDA_BASE = os.getenv('OPENFDA_BASE', 'https://api.fda.gov')
    for page in range(pages):
        skip = page * limit
        try:
            r = requests.get(
                f'{OPENFDA_BASE}/drug/enforcement.json',
                params={'limit': limit, 'skip': skip},
                timeout=30,
                headers={'User-Agent': 'MedVerify/Import'}
            )
            r.raise_for_status()
            results = r.json().get('results', [])
            log.info('  Page %d: %d enforcement records from OpenFDA', page + 1, len(results))
            for item in results:
                try:
                    recall_number = item.get('recall_number') or item.get('recall_initiation_date')
                    payload = {
                        'authority': 'US FDA',
                        'recall_number': recall_number,
                        'reason': item.get('reason_for_recall') or 'Drug Recall Notice.',
                        'affected_medicine': item.get('product_description') or '',
                        'source_url': item.get('report_date') or item.get('recall_initiation_date'),
                        'metadata': {'source': 'openfda_enforcement', 'recall_number': recall_number}
                    }
                    upsert_recall(client, payload)
                    total += 1
                except Exception as e:
                    log.debug('  recall upsert failed: %s', e)
        except Exception as e:
            log.warning('  OpenFDA recalls page %d failed: %s', page + 1, e)
        time.sleep(0.5)
    log.info('Phase 2 done: %d recalls upserted', total)
    return total

# -- 6. Phase 3: CDSCO Latest Alerts -> drug_alerts (PDF parse) ---------------
def run_cdsco_alerts(max_pdfs=3):
    log.info('=== Phase 3: CDSCO Latest Alerts -> drug_alerts (PDF) ===')
    import requests
    import tempfile
    from bs4 import BeautifulSoup
    from backend.app.scrapers.pdf_utils import download_pdf
    total = 0
    base_url = 'https://cdsco.gov.in'
    listing_url = os.getenv('CDSCO_ALERTS_URL', f'{base_url}/opencms/opencms/en/Latest-Alerts/')
    tmp_dir = tempfile.mkdtemp()

    try:
        r = requests.get(listing_url, timeout=15, headers={'User-Agent': 'MedVerify/Import'})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        pdf_links = []
        for a in soup.select('a'):
            href = a.get('href', '')
            if not href:
                continue
            lh = href.lower()
            if '.pdf' in lh or 'download_file_division.jsp' in lh or 'pdf-documents' in lh:
                full = requests.compat.urljoin(base_url, href)
                if full not in pdf_links:
                    pdf_links.append(full)
        log.info('  Found %d PDF links on CDSCO Alerts page', len(pdf_links))
        pdf_links = pdf_links[:max_pdfs]
    except Exception as e:
        log.warning('  CDSCO listing fetch failed: %s', e)
        return 0

    try:
        import pdfplumber
        import pandas as pd
    except ImportError:
        log.warning('  pdfplumber/pandas not available, skipping PDF parse')
        return 0

    for pdf_url in pdf_links:
        pdf_path = None
        try:
            # Resolves download_file_division.jsp automatically using our updated download_pdf helper
            pdf_path = download_pdf(pdf_url, tmp_dir)
            log.info('  Downloaded/Resolved PDF: %s (%d bytes)', os.path.basename(pdf_path), os.path.getsize(pdf_path))
        except Exception as e:
            log.warning('  PDF download failed %s: %s', pdf_url, e)
            continue

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        tbl = page.extract_table()
                        if tbl and len(tbl) >= 2:
                            df = pd.DataFrame(tbl[1:], columns=tbl[0])
                            for row in df.fillna('').to_dict(orient='records'):
                                normalized = {(k or '').strip().lower(): str(v).strip() for k, v in row.items()}
                                title = (
                                    normalized.get('name') or normalized.get('medicine') or
                                    normalized.get('drug') or normalized.get('subject') or
                                    normalized.get('reg no') or 'CDSCO Alert'
                                )[:500]
                                payload = {
                                    'title': title,
                                    'authority': 'CDSCO',
                                    'description': str(row)[:1000],
                                    'source_url': pdf_url,
                                    'metadata': {'source_pdf': os.path.basename(pdf_path), 'page': page_num + 1}
                                }
                                try:
                                    insert_alert(client, payload)
                                    total += 1
                                except Exception as ue:
                                    log.debug('  alert insert failed: %s', ue)
                        else:
                            text = page.extract_text() or ''
                            if text.strip():
                                payload = {
                                    'title': f'CDSCO Alert (page {page_num+1})',
                                    'authority': 'CDSCO',
                                    'description': text[:1000],
                                    'source_url': pdf_url,
                                    'metadata': {'source_pdf': os.path.basename(pdf_path), 'page': page_num + 1}
                                }
                                try:
                                    insert_alert(client, payload)
                                    total += 1
                                except Exception as ue:
                                    log.debug('  alert text insert failed: %s', ue)
                    except Exception as pe:
                        log.debug('  page %d extract failed: %s', page_num + 1, pe)
        except Exception as e:
            log.warning('  PDF parse failed %s: %s', pdf_path, e)

    log.info('Phase 3 done: %d drug_alert records inserted', total)
    return total

# -- 8. Phase 4: WHO Medical Product Alerts -> reports (which map to drug_alerts)
def run_who_alerts(max_links=10):
    log.info('=== Phase 4: WHO Medical Product Alerts -> drug_alerts ===')
    import requests
    from bs4 import BeautifulSoup
    total = 0
    who_url = os.getenv(
        'WHO_ALERTS_URL',
        'https://www.who.int/teams/regulation-prequalification/incidents-and-SF/full-list-of-who-medical-product-alerts'
    )
    try:
        r = requests.get(who_url, timeout=30, headers={'User-Agent': 'MedVerify/WHO-Import'})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')

        # Insert listing page
        title_tag = soup.find('h1') or soup.find('h2') or soup.title
        page_title = (title_tag.get_text(strip=True) if title_tag else 'WHO Medical Product Alerts')[:500]
        paragraphs = ' '.join(p.get_text(strip=True) for p in soup.find_all('p')[:5])
        try:
            upsert_who_alert(client, {
                'title': page_title,
                'summary': paragraphs[:2000],
                'authority': 'WHO GSMS',
                'source_url': who_url,
                'metadata': {'external_id': 'who-mpa-full-list'}
            })
            total += 1
            log.info('  Inserted WHO listing page')
        except Exception as e:
            log.debug('  WHO listing page insert failed: %s', e)

        # Collect links
        links = []
        for a in soup.select('a'):
            href = a.get('href', '')
            if not href:
                continue
            lh = href.lower()
            if 'medical-product-alert' in lh or '/news/item/' in lh or lh.endswith('.pdf'):
                full = requests.compat.urljoin(who_url, href)
                if full not in links:
                    links.append(full)
        log.info('  Found %d WHO alert links, processing up to %d', len(links), max_links)

        for link in links[:max_links]:
            try:
                pr = requests.get(link, timeout=20, headers={'User-Agent': 'MedVerify/WHO-Import'})
                pr.raise_for_status()
                ps = BeautifulSoup(pr.text, 'html.parser')
                t = ps.find('h1') or ps.find('h2') or ps.title
                title = (t.get_text(strip=True) if t else 'WHO Alert')[:500]
                body = ' '.join(p.get_text(strip=True) for p in ps.find_all('p')[:5])
                try:
                    upsert_who_alert(client, {
                        'title': title,
                        'summary': body[:2000],
                        'authority': 'WHO GSMS',
                        'source_url': link,
                        'metadata': {'link': link}
                    })
                    total += 1
                except Exception as ue:
                    log.debug('  WHO alert insert failed: %s', ue)
                time.sleep(0.3)
            except Exception as e:
                log.debug('  WHO link %s fetch failed: %s', link, e)
    except Exception as e:
        log.warning('  WHO alerts page fetch failed: %s', e)
    log.info('Phase 4 done: %d WHO reports/alerts upserted', total)
    return total

# -- 9. Main -------------------------------------------------------------------
def main():
    log.info('========== SafeMeds AI -- Full Database Import ==========')
    t0 = time.time()

    fda_labels  = run_openfda_labels(limit=100, pages=2)
    fda_recalls = run_openfda_recalls(limit=100, pages=1)
    cdsco_alerts= run_cdsco_alerts(max_pdfs=3)
    who_total   = run_who_alerts(max_links=10)

    elapsed = time.time() - t0
    log.info('Import finished in %.1f seconds', elapsed)

    log.info('')
    log.info('========== FINAL TABLE COUNTS ==========')
    tables = ['medicines', 'manufacturers', 'drug_alerts', 'drug_recalls', 'reports']
    counts = {}
    for tbl in tables:
        counts[tbl] = count_table(tbl)
        log.info('  %-20s : %d records', tbl, counts[tbl])

    log.info('')
    log.info('========== IMPORT SUMMARY ==========')
    log.info('  OpenFDA labels upserted  : %d', fda_labels)
    log.info('  OpenFDA recalls upserted : %d', fda_recalls)
    log.info('  CDSCO alerts inserted    : %d', cdsco_alerts)
    log.info('  WHO reports/alerts       : %d', who_total)

    any_populated = any(v > 0 for v in counts.values())
    if any_populated:
        log.info('')
        log.info('SUCCESS: Initial database population completed.')
    else:
        log.error('')
        log.error('FAILURE: All tables still empty -- check logs above for errors')
        sys.exit(1)

if __name__ == '__main__':
    main()

