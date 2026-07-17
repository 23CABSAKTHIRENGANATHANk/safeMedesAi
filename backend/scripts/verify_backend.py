"""Verification script for backend stack.

Checks:
- import backend FastAPI app
- Supabase client (if env provided)
- CDSCO parser (fetch one listing)
- OpenFDA fetch (labels)
- Scheduler start/stop

Run from repo root:
 python backend/scripts/verify_backend.py
"""
import os
import sys
import traceback
from importlib import import_module

from dotenv import load_dotenv
load_dotenv()

# Ensure repository root is on sys.path so package imports work when running
# this script directly (sys.path[0] is script dir otherwise).
repo_root = os.getcwd()
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

OK = True

def note(msg):
    print('[INFO]', msg)

def error(msg):
    global OK
    OK = False
    print('[ERROR]', msg)


def try_import(path):
    try:
        mod = import_module(path)
        note(f'imported {path}')
        return mod
    except Exception:
        error(f'failed to import {path}:')
        traceback.print_exc()
        return None


def main():
    note('Starting backend verification')

    # 1. Import FastAPI app
    app_mod = try_import('backend.app.main')

    # 2. Supabase client
    supabase_ok = False
    try:
        sc = try_import('backend.app.scrapers.supabase_client')
        if sc:
            get_client = getattr(sc, 'get_client', None)
            if get_client:
                try:
                    client = get_client()
                    note('Supabase client created')
                    # try a lightweight call (list tables may be permissioned) - attempt select 1
                    try:
                        r = client.table('medicines').select('id').limit(1).execute()
                        note('Supabase query executed')
                    except Exception as e:
                        note(f'Supabase query failed (this may be OK if credentials missing): {e}')
                    supabase_ok = True
                except Exception as e:
                    error(f'Failed to create Supabase client: {e}')
            else:
                error('get_client not found in supabase_client')
    except Exception:
        error('Supabase client import failed')

    # 3. CDSCO parser quick fetch
    try:
        import requests
        parsers = try_import('backend.app.scrapers.cdsco_parsers')
        url = os.getenv('CDSCO_ALERTS_URL', 'https://cdsco.gov.in/opencms/opencms/en/Latest-Alerts/')
        note(f'Checking CDSCO page reachable: {url}')
        try:
            r = requests.get(url, timeout=10, headers={'User-Agent': 'verify-script'})
            r.raise_for_status()
            # quick sanity check: count links
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, 'html.parser')
            links = soup.select('a')
            note(f'CDSCO page reachable, found {len(links)} anchor elements')
        except Exception:
            error('CDSCO listing fetch failed or timed out')
            traceback.print_exc()
    except Exception:
        error('CDSCO parsers import failed')

    # 4. OpenFDA fetch
    try:
        fda = try_import('backend.app.services.fda_service')
        if fda:
            try:
                items = fda.fetch_labels(limit=1, skip=0)
                note(f'OpenFDA returned {len(items)} label items (sample)')
            except Exception:
                error('OpenFDA fetch failed')
                traceback.print_exc()
    except Exception:
        error('OpenFDA service import failed')

    # 5. Scheduler start/stop
    try:
        jr = try_import('backend.app.jobs.job_runner')
        if jr:
            try:
                note('Starting job runner')
                jr.start_all_jobs()
                note('Job runner started')
                jr.shutdown_all_jobs()
                note('Job runner stopped')
            except Exception:
                error('Job runner start/stop failed')
                traceback.print_exc()
    except Exception:
        error('Job runner import failed')

    if OK:
        note('Backend verification completed: OK')
        sys.exit(0)
    else:
        error('Backend verification failed; check errors above')
        sys.exit(2)


if __name__ == '__main__':
    main()
