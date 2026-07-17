"""Supabase client and upsert services for scraping pipeline."""
import os
import logging
from supabase import create_client
from typing import Any, Dict

log = logging.getLogger('scraper.supabase')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def get_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError('SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in env')
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def upsert_medicine(client, medicine: Dict[str, Any]):
    # medicine: {name, form, strength, manufacturer, batch, primary_identifier, metadata}
    # Use normalized_name uniqueness guard in DB
    payload = {
        'name': medicine.get('name'),
        'form': medicine.get('form'),
        'strength': medicine.get('strength'),
        'manufacturer_id': None,
        'batch_number': medicine.get('batch'),
        'primary_identifier': medicine.get('primary_identifier'),
        'metadata': medicine.get('metadata') or {}
    }
    try:
        res = client.table('medicines').upsert(payload, on_conflict=['normalized_name', 'manufacturer_id', 'form', 'strength']).execute()
        log.info('Upserted medicine %s', payload.get('name'))
        return res
    except Exception:
        log.exception('supabase upsert medicine failed')
        raise

def insert_alert(client, alert: Dict[str, Any]):
    try:
        res = client.table('drug_alerts').insert(alert).execute()
        log.info('Inserted alert')
        return res
    except Exception:
        log.exception('insert alert failed')
        raise

def insert_recall(client, recall: Dict[str, Any]):
    try:
        res = client.table('drug_recalls').insert(recall).execute()
        log.info('Inserted recall')
        return res
    except Exception:
        log.exception('insert recall failed')
        raise

def upsert_recall(client, recall: Dict[str, Any]):
    # upsert based on recall_number or external id field
    try:
        conflict_cols = ['recall_number'] if 'recall_number' in recall else ['source_url']
        res = client.table('drug_recalls').upsert(recall, on_conflict=conflict_cols).execute()
        log.info('Upserted recall %s', recall.get('recall_number') or recall.get('source_url'))
        return res
    except Exception:
        log.exception('supabase upsert recall failed')
        raise

def upsert_report(client, report: Dict[str, Any]):
    try:
        conflict_cols = ['external_id'] if 'external_id' in report else []
        if conflict_cols:
            res = client.table('reports').upsert(report, on_conflict=conflict_cols).execute()
        else:
            res = client.table('reports').insert(report).execute()
        log.info('Inserted/upserted report')
        return res
    except Exception:
        log.exception('upsert report failed')
        raise

def upsert_who_alert(client, alert: Dict[str, Any]):
    """Upsert WHO alert into `reports` table using `external_id` or `title` to dedupe."""
    try:
        conflict_cols = ['external_id'] if 'external_id' in alert else ['title']
        res = client.table('reports').upsert(alert, on_conflict=conflict_cols).execute()
        log.info('Upserted WHO alert %s', alert.get('external_id') or alert.get('title'))
        return res
    except Exception:
        log.exception('upsert who alert failed')
        raise
