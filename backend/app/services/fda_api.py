"""FastAPI router exposing OpenFDA-backed endpoints."""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
import logging
from .fda_service import refresh_all_to_supabase
from ..scrapers.supabase_client import get_client

log = logging.getLogger('api.fda')
router = APIRouter(prefix='/api/fda', tags=['fda'])


@router.get('/labels')
def get_labels(page: int = 1, limit: int = 100):
    try:
        client = get_client()
        start = (page - 1) * limit
        end = start + limit - 1
        res = client.table('medicines').select('*').range(start, end).execute()
        return res.data if hasattr(res, 'data') else res
    except Exception:
        log.exception('get_labels failed')
        raise HTTPException(status_code=500, detail='failed to get labels')


@router.get('/recalls')
def get_recalls(page: int = 1, limit: int = 100):
    try:
        client = get_client()
        start = (page - 1) * limit
        end = start + limit - 1
        res = client.table('drug_recalls').select('*').range(start, end).execute()
        return res.data if hasattr(res, 'data') else res
    except Exception:
        log.exception('get_recalls failed')
        raise HTTPException(status_code=500, detail='failed to get recalls')


@router.get('/events')
def get_events(page: int = 1, limit: int = 100):
    try:
        client = get_client()
        start = (page - 1) * limit
        end = start + limit - 1
        res = client.table('reports').select('*').range(start, end).execute()
        return res.data if hasattr(res, 'data') else res
    except Exception:
        log.exception('get_events failed')
        raise HTTPException(status_code=500, detail='failed to get events')


@router.get('/search')
def search(medicine: str = Query(..., min_length=2), page: int = 1, limit: int = 50):
    try:
        client = get_client()
        start = (page - 1) * limit
        end = start + limit - 1
        # use ilike for case-insensitive contains
        res = client.table('medicines').select('*').filter('name', 'ilike', f'%{medicine}%').range(start, end).execute()
        return res.data if hasattr(res, 'data') else res
    except Exception:
        log.exception('search failed')
        raise HTTPException(status_code=500, detail='search failed')


@router.post('/refresh')
def refresh(limit: int = 100, pages: int = 1):
    """Trigger a manual refresh from OpenFDA into Supabase."""
    try:
        total = refresh_all_to_supabase(limit=limit, pages=pages)
        return {'refreshed': total}
    except Exception:
        log.exception('refresh failed')
        raise HTTPException(status_code=500, detail='refresh failed')
