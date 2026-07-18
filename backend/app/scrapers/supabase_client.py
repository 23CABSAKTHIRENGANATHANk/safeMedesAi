"""Supabase client and upsert services for scraping pipeline."""
import os
import logging
from dotenv import load_dotenv
from supabase import create_client
from typing import Any, Dict

load_dotenv()
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
    manufacturer_name = medicine.get('manufacturer')
    manufacturer_id = None
    if manufacturer_name:
        try:
            m_name_clean = manufacturer_name.strip()
            if m_name_clean:
                # Query existing manufacturer
                m_res = client.table('manufacturers').select('id').eq('name', m_name_clean).execute()
                m_data = m_res.data if hasattr(m_res, 'data') else m_res
                if m_data:
                    manufacturer_id = m_data[0]['id']
                else:
                    # Insert new manufacturer
                    ins_res = client.table('manufacturers').insert({'name': m_name_clean}).execute()
                    ins_data = ins_res.data if hasattr(ins_res, 'data') else ins_res
                    if ins_data:
                        manufacturer_id = ins_data[0]['id']
        except Exception:
            log.exception('Failed to look up or insert manufacturer: %s', manufacturer_name)

    metadata = medicine.get('metadata') or {}
    if medicine.get('batch') and 'batch' not in metadata:
        metadata['batch'] = medicine.get('batch')

    payload = {
        'name': medicine.get('name'),
        'form': medicine.get('form'),
        'strength': medicine.get('strength'),
        'manufacturer_id': manufacturer_id,
        'primary_identifier': medicine.get('primary_identifier'),
        'metadata': metadata
    }
    try:
        q = client.table('medicines').select('id').eq('name', payload['name'])
        if payload.get('manufacturer_id'):
            q = q.eq('manufacturer_id', payload['manufacturer_id'])
        else:
            q = q.is_('manufacturer_id', 'null')
        if payload.get('form'):
            q = q.eq('form', payload['form'])
        else:
            q = q.is_('form', 'null')
        if payload.get('strength'):
            q = q.eq('strength', payload['strength'])
        else:
            q = q.is_('strength', 'null')

        m_res = q.execute()
        m_data = m_res.data if hasattr(m_res, 'data') else m_res
        if m_data:
            res = client.table('medicines').update(payload).eq('id', m_data[0]['id']).execute()
            log.info('Updated medicine %s', payload.get('name'))
            return res
        else:
            res = client.table('medicines').insert(payload).execute()
            log.info('Inserted medicine %s', payload.get('name'))
            return res
    except Exception:
        log.exception('supabase custom upsert medicine failed, trying insert fallback')
        try:
            res = client.table('medicines').insert(payload).execute()
            log.info('Inserted medicine (fallback) %s', payload.get('name'))
            return res
        except Exception:
            log.exception('supabase fallback insert medicine failed')
            raise

def insert_alert(client, alert: Dict[str, Any]):
    medicine_id = None
    title = alert.get('title') or alert.get('name')
    if title:
        try:
            m_res = client.table('medicines').select('id').ilike('name', f'%{title}%').limit(1).execute()
            if m_res.data:
                medicine_id = m_res.data[0]['id']
        except Exception:
            pass

    payload = {
        'medicine_id': medicine_id,
        'manufacturer_id': alert.get('manufacturer_id'),
        'authority': alert.get('authority') or 'CDSCO',
        'alert_code': alert.get('alert_code'),
        'alert_type': alert.get('alert_type'),
        'severity': alert.get('severity') or 'medium',
        'title': title,
        'summary': alert.get('summary') or alert.get('description'),
        'details': alert.get('details') or alert.get('description'),
        'effective_date': alert.get('effective_date'),
        'expires_at': alert.get('expires_at'),
        'source_url': alert.get('source_url'),
        'raw_payload': alert.get('raw_payload') or alert.get('metadata') or alert
    }
    try:
        res = client.table('drug_alerts').insert(payload).execute()
        log.info('Inserted alert')
        return res
    except Exception:
        log.exception('insert alert failed')
        raise

def map_recall_payload(client, recall: Dict[str, Any]) -> Dict[str, Any]:
    medicine_id = None
    affected = recall.get('affected_medicine') or recall.get('title')
    if affected:
        try:
            m_res = client.table('medicines').select('id').ilike('name', f'%{affected}%').limit(1).execute()
            if m_res.data:
                medicine_id = m_res.data[0]['id']
        except Exception:
            pass

    payload = {
        'medicine_id': medicine_id,
        'manufacturer_id': recall.get('manufacturer_id'),
        'authority': recall.get('authority') or 'US FDA',
        'recall_number': recall.get('recall_number'),
        'recall_level': recall.get('recall_level'),
        'reason': recall.get('reason') or recall.get('title'),
        'status': recall.get('status') or 'open',
        'source_url': recall.get('source_url'),
        'raw_payload': recall.get('raw_payload') or recall.get('metadata') or recall
    }
    return payload

def insert_recall(client, recall: Dict[str, Any]):
    payload = map_recall_payload(client, recall)
    try:
        res = client.table('drug_recalls').insert(payload).execute()
        log.info('Inserted recall')
        return res
    except Exception:
        log.exception('insert recall failed')
        raise

def upsert_recall(client, recall: Dict[str, Any]):
    payload = map_recall_payload(client, recall)
    try:
        r_res = None
        if payload.get('recall_number'):
            r_res = client.table('drug_recalls').select('id').eq('recall_number', payload['recall_number']).execute()
        elif payload.get('source_url'):
            r_res = client.table('drug_recalls').select('id').eq('source_url', payload['source_url']).execute()

        r_data = r_res.data if r_res and hasattr(r_res, 'data') else r_res
        if r_data:
            res = client.table('drug_recalls').update(payload).eq('id', r_data[0]['id']).execute()
            log.info('Updated recall %s', payload.get('recall_number') or payload.get('source_url'))
            return res
        else:
            res = client.table('drug_recalls').insert(payload).execute()
            log.info('Inserted recall %s', payload.get('recall_number') or payload.get('source_url'))
            return res
    except Exception:
        log.exception('supabase custom upsert recall failed, trying insert fallback')
        try:
            res = client.table('drug_recalls').insert(payload).execute()
            log.info('Inserted recall (fallback) %s', payload.get('recall_number') or payload.get('source_url'))
            return res
        except Exception:
            log.exception('supabase fallback insert recall failed')
            raise

def upsert_report(client, report: Dict[str, Any]):
    # Map reports (like adverse events) to drug_alerts
    payload = {
        'authority': 'OpenFDA Event',
        'title': f"Safety Report {report.get('external_id') or ''}",
        'summary': report.get('summary'),
        'raw_payload': report.get('metadata') or report
    }
    try:
        res = client.table('drug_alerts').insert(payload).execute()
        log.info('Inserted report as drug alert')
        return res
    except Exception:
        log.exception('upsert report failed')
        raise

def upsert_who_alert(client, alert: Dict[str, Any]):
    payload = {
        'authority': alert.get('authority') or 'WHO GSMS',
        'title': alert.get('title'),
        'summary': alert.get('summary'),
        'details': alert.get('affected_product'),
        'source_url': alert.get('metadata', {}).get('source_url') or alert.get('source_url'),
        'raw_payload': alert.get('metadata') or alert
    }
    try:
        res = client.table('drug_alerts').insert(payload).execute()
        log.info('Upserted WHO alert as drug alert')
        return res
    except Exception:
        log.exception('upsert who alert failed')
        raise
