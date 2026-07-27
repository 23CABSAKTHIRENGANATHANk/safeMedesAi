from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import Optional
import logging
from sqlalchemy.orm import Session
from ..scrapers.supabase_client import get_client
from ..services.fda_service import fetch_openfda
from ..services.gemini_service import summarize_medicine
from ..database import get_db
from ..models.medicine import MedicineRecord

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
def list_medicines(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    try:
        start, end = _get_range(page, limit)
        try:
            client = get_client()
            res = client.table('medicines').select('*').range(start, end).execute()
            return res.data if hasattr(res, 'data') else res
        except Exception as e:
            log.warning('Supabase query failed, falling back to local SQLite: %s', e)
            offset = start
            records = db.query(MedicineRecord).offset(offset).limit(limit).all()
            return [
                {
                    'id': r.id,
                    'name': r.name,
                    'batch': r.batch,
                    'manufacturer': r.manufacturer,
                    'status': r.status,
                    'authority': r.authority,
                    'reason': r.reason,
                    'created_at': r.created_at.isoformat() if r.created_at else None
                }
                for r in records
            ]
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get('/api/medicine/{name}')
def get_medicine(name: str = Path(..., min_length=1), db: Session = Depends(get_db)):
    try:
        try:
            client = get_client()
            # try exact match first
            res = client.table('medicines').select('*').filter('name', 'eq', name).limit(1).execute()
            data = res.data if hasattr(res, 'data') else res
            if data:
                record = data[0]
                # aggregate related data and summarize
                alerts_res = client.table('drug_alerts').select('*').filter('title', 'ilike', f'%{name}%').limit(10).execute()
                # Note: drug_recalls has no 'affected_medicine' column; search 'reason' instead
                recalls_res = client.table('drug_recalls').select('*').filter('reason', 'ilike', f'%{name}%').limit(10).execute()
                alerts = alerts_res.data if hasattr(alerts_res, 'data') else []
                recalls = recalls_res.data if hasattr(recalls_res, 'data') else []
                # reports table may not exist; wrap defensively
                reports = []
                try:
                    reports_res = client.table('reports').select('*').filter('title', 'ilike', f'%{name}%').limit(10).execute()
                    reports = reports_res.data if hasattr(reports_res, 'data') else []
                except Exception:
                    reports = []
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
                return {
                    'medicine': record,
                    'alerts': [],
                    'recalls': [],
                    'reports': [],
                    'fda': None,
                    'ai_summary': None
                }
            raise HTTPException(status_code=404, detail='medicine not found')
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            log.warning('Supabase query failed, falling back to local SQLite: %s', e)
            
            # Try to find matching record in SQLite
            match = db.query(MedicineRecord).filter(
                MedicineRecord.name.ilike(name)
            ).first()
            if not match:
                # If exact name check fails, try a substring match
                match = db.query(MedicineRecord).filter(
                    MedicineRecord.name.ilike(f'%{name}%')
                ).first()
                
            if not match:
                raise HTTPException(status_code=404, detail='medicine not found')
                
            return {
                'medicine': {
                    'id': match.id,
                    'name': match.name,
                    'batch': match.batch,
                    'manufacturer': match.manufacturer,
                    'status': match.status,
                    'authority': match.authority,
                    'reason': match.reason,
                    'created_at': match.created_at.isoformat() if match.created_at else None
                },
                'alerts': [],
                'recalls': [],
                'reports': [],
                'fda': None,
                'ai_summary': f"Synthesized Clinical Profile (Offline Local Mode):\n\n**Medicine**: {match.name}\n**Batch**: {match.batch or 'N/A'}\n**Manufacturer**: {match.manufacturer or 'Generic'}\n**Safety Status**: {match.status.upper()} (Authority: {match.authority})\n\n*Note: Detailed historical alerts, recall logs, and OpenFDA records are currently unavailable because the application is running in local fallback mode.*"
            }
    except HTTPException:
        raise
    except Exception:
        log.exception('get_medicine failed')
        raise HTTPException(status_code=500, detail='failed to fetch medicine')


@router.get('/api/alerts')
def list_alerts(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    try:
        start, end = _get_range(page, limit)
        try:
            client = get_client()
            res = client.table('drug_alerts').select('*').range(start, end).execute()
            return res.data if hasattr(res, 'data') else res
        except Exception as e:
            log.warning('Supabase query failed, falling back to local SQLite alerts: %s', e)
            # Alerts in local DB are warnings or unsafe records
            offset = start
            records = db.query(MedicineRecord).filter(
                MedicineRecord.status.in_(['warning', 'unsafe'])
            ).offset(offset).limit(limit).all()
            return [
                {
                    'id': r.id,
                    'authority': r.authority,
                    'title': f"Alert: {r.name} ({r.status.upper()})",
                    'description': r.reason,
                    'date': r.created_at.isoformat() if r.created_at else None,
                    'metadata': {'local': True, 'batch': r.batch, 'manufacturer': r.manufacturer}
                }
                for r in records
            ]
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.get('/api/recalls')
def list_recalls(
    page: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    try:
        start, end = _get_range(page, limit)
        try:
            client = get_client()
            res = client.table('drug_recalls').select('*').range(start, end).execute()
            return res.data if hasattr(res, 'data') else res
        except Exception as e:
            log.warning('Supabase query failed, falling back to local SQLite recalls: %s', e)
            # Recalls in local DB are unsafe records
            offset = start
            records = db.query(MedicineRecord).filter(
                MedicineRecord.status == 'unsafe'
            ).offset(offset).limit(limit).all()
            return [
                {
                    'id': r.id,
                    'authority': r.authority,
                    'title': f"Recall: {r.name} - Batch {r.batch or 'All'}",
                    'description': r.reason,
                    'date': r.created_at.isoformat() if r.created_at else None,
                    'metadata': {'local': True, 'batch': r.batch, 'manufacturer': r.manufacturer}
                }
                for r in records
            ]
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        log.exception('list_recalls failed')
        raise HTTPException(status_code=500, detail='failed to list recalls')


@router.get('/api/search')
def search_medicines(
    medicine: str = Query(..., min_length=2),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    try:
        start, end = _get_range(page, limit)
        try:
            client = get_client()
            res = client.table('medicines').select('*').filter('name', 'ilike', f'%{medicine}%').range(start, end).execute()
            return res.data if hasattr(res, 'data') else res
        except Exception as e:
            log.warning('Supabase query failed, falling back to local SQLite search: %s', e)
            offset = start
            records = db.query(MedicineRecord).filter(
                MedicineRecord.name.ilike(f'%{medicine}%')
            ).offset(offset).limit(limit).all()
            return [
                {
                    'id': r.id,
                    'name': r.name,
                    'batch': r.batch,
                    'manufacturer': r.manufacturer,
                    'status': r.status,
                    'authority': r.authority,
                    'reason': r.reason,
                    'created_at': r.created_at.isoformat() if r.created_at else None
                }
                for r in records
            ]
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        log.exception('search_medicines failed')
        raise HTTPException(status_code=500, detail='failed to search medicines')


@router.post('/api/admin/import-datasets')
def trigger_dataset_import(
    supabase: bool = Query(False),
    reset: bool = Query(False),
    db: Session = Depends(get_db)
):
    try:
        from backend.scripts.import_datasets import import_local_sqlite, import_supabase
        import os
        
        # Setup paths
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__)) # api/
        APP_DIR = os.path.dirname(SCRIPT_DIR) # app/
        BACKEND_DIR = os.path.dirname(APP_DIR) # backend/
        REPO_ROOT = os.path.dirname(BACKEND_DIR) # root
        
        datasets_dir = os.path.join(REPO_ROOT, "datasets")
        if not os.path.exists(datasets_dir):
            raise HTTPException(status_code=404, detail=f"Datasets directory not found at {datasets_dir}")
            
        import_local_sqlite(datasets_dir, reset=reset)
        if supabase:
            import_supabase(datasets_dir)
            
        return {"status": "success", "message": "Datasets imported successfully."}
    except Exception as e:
        log.exception("Import failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/api/admin/counts')
def get_database_counts(db: Session = Depends(get_db)):
    local_meds = db.query(MedicineRecord).count()
    try:
        from backend.app.models.manufacturer import Manufacturer
        local_mfgs = db.query(Manufacturer).count()
    except Exception:
        local_mfgs = 0
        
    supabase_counts = {}
    try:
        client = get_client()
        for table in ['medicines', 'manufacturers', 'drug_alerts', 'drug_recalls', 'reports']:
            try:
                res = client.table(table).select('*', count='exact').limit(1).execute()
                supabase_counts[table] = res.count if hasattr(res, 'count') and res.count is not None else 0
            except Exception as e:
                supabase_counts[table] = f"Error: {str(e)}"
    except Exception as e:
        supabase_counts["error"] = str(e)
        
    return {
        "local_sqlite": {
            "medicine_records": local_meds,
            "manufacturers": local_mfgs
        },
        "supabase_postgres": supabase_counts
    }


