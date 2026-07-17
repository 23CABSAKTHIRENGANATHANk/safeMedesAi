"""Service to fetch and normalize data from the OpenFDA API."""
from typing import Dict, Any, List, Optional
import logging
import os
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from . import __name__ as pkg
from ..scrapers.supabase_client import get_client, upsert_medicine, upsert_recall, upsert_report

log = logging.getLogger('service.fda')

OPENFDA_BASE = os.getenv('OPENFDA_BASE', 'https://api.fda.gov')
DEFAULT_LIMIT = int(os.getenv('OPENFDA_PAGE_LIMIT', '100'))
DEFAULT_TIMEOUT = int(os.getenv('OPENFDA_TIMEOUT', '30'))


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), retry=retry_if_exception_type(Exception))
def fetch_openfda(endpoint: str, params: Optional[Dict[str, Any]] = None, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    url = f"{OPENFDA_BASE}/{endpoint}"
    log.debug('OpenFDA fetch %s %s', url, params)
    r = requests.get(url, params=params, timeout=timeout, headers={'User-Agent': 'MedVerify/OpenFDA-Client'})
    r.raise_for_status()
    return r.json()


def normalize_label_item(item: Dict[str, Any]) -> Dict[str, Any]:
    # Map relevant fields from label to medicine record
    name = item.get('openfda', {}).get('generic_name') or item.get('openfda', {}).get('brand_name')
    manufacturer = None
    if 'openfda' in item and 'manufacturer_name' in item['openfda']:
        m = item['openfda']['manufacturer_name']
        manufacturer = m[0] if isinstance(m, list) else m
    record = {
        'name': name,
        'form': item.get('dosage_and_administration') or item.get('dosage_and_administration_statement'),
        'strength': None,
        'manufacturer': manufacturer,
        'primary_identifier': item.get('id'),
        'metadata': {'source': 'openfda_label', 'raw': item}
    }
    return record


def fetch_labels(limit: int = DEFAULT_LIMIT, skip: int = 0) -> List[Dict[str, Any]]:
    params = {'limit': limit, 'skip': skip}
    data = fetch_openfda('drug/label.json', params=params)
    results = data.get('results', [])
    normalized = [normalize_label_item(i) for i in results]
    return normalized


def normalize_recall_item(item: Dict[str, Any]) -> Dict[str, Any]:
    recall_number = item.get('recall_number') or item.get('recall_initiation_date')
    return {
        'title': item.get('product_description') or item.get('reason_for_recall') or 'Recall',
        'recall_number': recall_number,
        'reason': item.get('reason_for_recall'),
        'affected_medicine': item.get('product_description'),
        'source_url': item.get('report_date') or item.get('recall_initiation_date'),
        'metadata': {'source': 'openfda_enforcement', 'raw': item}
    }


def fetch_recalls(limit: int = DEFAULT_LIMIT, skip: int = 0) -> List[Dict[str, Any]]:
    params = {'limit': limit, 'skip': skip}
    data = fetch_openfda('drug/enforcement.json', params=params)
    results = data.get('results', [])
    return [normalize_recall_item(i) for i in results]


def normalize_event_item(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        'external_id': item.get('safetyreportid') or item.get('id'),
        'summary': item.get('serious') or None,
        'metadata': {'source': 'openfda_event', 'raw': item}
    }


def fetch_events(limit: int = DEFAULT_LIMIT, skip: int = 0) -> List[Dict[str, Any]]:
    params = {'limit': limit, 'skip': skip}
    data = fetch_openfda('drug/event.json', params=params)
    results = data.get('results', [])
    return [normalize_event_item(i) for i in results]


def refresh_all_to_supabase(limit: int = 100, pages: int = 1):
    """Fetch pages of OpenFDA data and upsert into Supabase.

    limit: items per page
    pages: number of pages to fetch sequentially
    """
    client = get_client()
    total = 0
    for p in range(pages):
        skip = p * limit
        # labels
        try:
            labels = fetch_labels(limit=limit, skip=skip)
            for l in labels:
                try:
                    upsert_medicine(client, l)
                    total += 1
                except Exception:
                    log.exception('failed upsert label')
        except Exception:
            log.exception('fetch labels failed')

        # recalls
        try:
            recalls = fetch_recalls(limit=limit, skip=skip)
            for r in recalls:
                try:
                    upsert_recall(client, r)
                    total += 1
                except Exception:
                    log.exception('failed upsert recall')
        except Exception:
            log.exception('fetch recalls failed')

        # events
        try:
            events = fetch_events(limit=limit, skip=skip)
            for e in events:
                try:
                    upsert_report(client, e)
                    total += 1
                except Exception:
                    log.exception('failed upsert event')
        except Exception:
            log.exception('fetch events failed')

    log.info('Refreshed %d OpenFDA records into Supabase', total)
    return total
