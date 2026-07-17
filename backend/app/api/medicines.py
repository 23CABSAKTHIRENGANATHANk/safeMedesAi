from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional
import logging
from ..scrapers.supabase_client import get_client
from ..services.fda_service import fetch_openfda
from ..services.gemini_service import summarize_medicine

router = APIRouter()
log = logging.getLogger('api.medicines')


def _get_range(page: int, limit: int):
    if page < 1:
        raise ValueError('page must be >= 1')
    if not (1 <= limit <= 1000):
        raise ValueError('limit must be between 1 and 1000')
    start = (page - 1) * limit
    end = start + limit - 1
    return start, end


@router.get('/api/medicines')
def list_medicines(page: int = Query(1, ge=1), limit: int = Query(100, ge=1, le=1000)):
    try:
        start, end = _get_range(page, limit)
        try:
            client = get_client()
        except Exception as e:
            log.warning('Supabase client unavailable: %s', e)
            raise HTTPException(status_code=503, detail='Supabase not configured or unreachable')
        res = client.table('medicines').select('*').range(start, end).execute()
        return res.data if hasattr(res, 'data') else res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get('/api/medicine/{name}')
def get_medicine(name: str = Path(..., min_length=1)):
    try:
        try:
            client = get_client()
        except Exception as e:
            log.warning('Supabase client unavailable: %s', e)
            raise HTTPException(status_code=503, detail='Supabase not configured or unreachable')
        # try exact match first
        res = client.table('medicines').select('*').filter('name', 'eq', name).limit(1).execute()
        data = res.data if hasattr(res, 'data') else res
        if data:
            record = data[0]
            # aggregate related data and summarize
            alerts_res = client.table('drug_alerts').select('*').filter('title', 'ilike', f'%{name}%').limit(10).execute()
            recalls_res = client.table('drug_recalls').select('*').filter('affected_medicine', 'ilike', f'%{name}%').limit(10).execute()
            reports_res = client.table('reports').select('*').filter('title', 'ilike', f'%{name}%').limit(10).execute()
            alerts = alerts_res.data if hasattr(alerts_res, 'data') else alerts_res
            recalls = recalls_res.data if hasattr(recalls_res, 'data') else recalls_res
            reports = reports_res.data if hasattr(reports_res, 'data') else reports_res
            # call OpenFDA for additional context (best-effort)
            fda_results = None
            try:
                fda_results = fetch_openfda('drug/label.json', params={'search': name, 'limit': 5})
            except Exception:
                fda_results = None

            # CDSCO notes: attempt to find CDSCO-origin alerts in alerts/recalls metadata
            cdsco_notes = []
            try:
                for a in (alerts or []):
                    meta = a.get('metadata') or {}
                    if meta.get('source_pdf') or meta.get('nsq') or 'cdsco' in (a.get('source_url') or '').lower():
                        cdsco_notes.append(a)
            except Exception:
                cdsco_notes = []

            context = {
                'supabase_medicine': record,
                'alerts': alerts,
                'recalls': recalls,
                'reports': reports,
                'fda': fda_results,
                'cdsco': cdsco_notes,
            }

            ai_summary = None
            try:
                ai_summary = summarize_medicine(name, context)
            except Exception:
                log.exception('AI summarization failed')
                ai_summary = None

            return {'medicine': record, 'alerts': alerts, 'recalls': recalls, 'reports': reports, 'fda': fda_results, 'ai_summary': ai_summary}
        # fallback to case-insensitive contains
        res = client.table('medicines').select('*').filter('name', 'ilike', f'%{name}%').limit(1).execute()
        data = res.data if hasattr(res, 'data') else res
        if data:
            record = data[0]
            # minimal aggregation for fallback
            return {'medicine': record}
        raise HTTPException(status_code=404, detail='medicine not found')
    except HTTPException:
        raise
    except Exception:
        log.exception('get_medicine failed')
        raise HTTPException(status_code=500, detail='failed to fetch medicine')


@router.get('/api/alerts')
def list_alerts(page: int = Query(1, ge=1), limit: int = Query(100, ge=1, le=1000)):
    try:
        start, end = _get_range(page, limit)
        try:
            client = get_client()
        except Exception as e:
            log.warning('Supabase client unavailable: %s', e)
            raise HTTPException(status_code=503, detail='Supabase not configured or unreachable')
        res = client.table('drug_alerts').select('*').range(start, end).execute()
        return res.data if hasattr(res, 'data') else res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get('/api/recalls')
def list_recalls(page: int = Query(1, ge=1), limit: int = Query(100, ge=1, le=1000)):
    try:
        start, end = _get_range(page, limit)
        try:
            client = get_client()
        except Exception as e:
            log.warning('Supabase client unavailable: %s', e)
            raise HTTPException(status_code=503, detail='Supabase not configured or unreachable')
        res = client.table('drug_recalls').select('*').range(start, end).execute()
        return res.data if hasattr(res, 'data') else res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        log.exception('list_recalls failed')
        raise HTTPException(status_code=500, detail='failed to list recalls')


@router.get('/api/search')
def search_medicines(medicine: str = Query(..., min_length=2), page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=1000)):
    try:
        start, end = _get_range(page, limit)
        try:
            client = get_client()
        except Exception as e:
            log.warning('Supabase client unavailable: %s', e)
            raise HTTPException(status_code=503, detail='Supabase not configured or unreachable')
        res = client.table('medicines').select('*').filter('name', 'ilike', f'%{medicine}%').range(start, end).execute()
        return res.data if hasattr(res, 'data') else res
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        log.exception('search_medicines failed')
        raise HTTPException(status_code=500, detail='failed to search medicines')
