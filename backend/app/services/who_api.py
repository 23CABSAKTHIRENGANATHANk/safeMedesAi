"""FastAPI router for WHO alerts scraper controls and listing."""
from fastapi import APIRouter, HTTPException
import logging
from ..scrapers.supabase_client import get_client
from .who_service import ingest_who_listing

router = APIRouter(prefix='/api/who', tags=['who'])
log = logging.getLogger('api.who')


@router.post('/refresh')
def refresh():
    try:
        count = ingest_who_listing()
        return {'ingested': count}
    except Exception:
        log.exception('who refresh failed')
        raise HTTPException(status_code=500, detail='refresh failed')


@router.get('/alerts')
def alerts(page: int = 1, limit: int = 100):
    try:
        client = get_client()
        start = (page - 1) * limit
        end = start + limit - 1
        res = client.table('reports').select('*').filter('source', 'eq', 'who').range(start, end).execute()
        return res.data if hasattr(res, 'data') else res
    except Exception:
        log.exception('who alerts failed')
        raise HTTPException(status_code=500, detail='failed to fetch alerts')
