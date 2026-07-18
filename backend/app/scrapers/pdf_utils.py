"""PDF helpers for downloading and extracting tables."""
from typing import List
import os
import logging
from .http import fetch
import pdfplumber
import pandas as pd

log = logging.getLogger('scraper.pdf')

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def download_pdf(url: str, dest_dir: str) -> str:
    ensure_dir(dest_dir)
    if 'download_file_division.jsp' in url.lower():
        from bs4 import BeautifulSoup
        import requests
        resp = fetch(url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        iframe = soup.find('iframe')
        if iframe and iframe.get('src'):
            url = requests.compat.urljoin(url, iframe.get('src'))
            log.info('Resolved JSP division to actual PDF: %s', url)

    resp = fetch(url, stream=True)
    filename = os.path.basename(url.split('?')[0]) or 'download.pdf'
    if not filename.lower().endswith('.pdf'):
        filename = filename + '.pdf'
    safe_path = os.path.join(dest_dir, filename)
    with open(safe_path, 'wb') as f:
        for chunk in resp.iter_content(1024 * 32):
            if chunk:
                f.write(chunk)
    log.info('Downloaded PDF %s', safe_path)
    return safe_path

def extract_tables(path: str) -> List[pd.DataFrame]:
    dfs = []
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                try:
                    tbl = page.extract_table()
                    if tbl and len(tbl) > 1:
                        df = pd.DataFrame(tbl[1:], columns=tbl[0])
                        dfs.append(df)
                except Exception:
                    log.exception('table extract failed on page')
    except Exception:
        log.exception('open pdf failed')
    return dfs
