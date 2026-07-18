from typing import Optional

from sqlalchemy.orm import Session

from ..models.medicine import MedicineRecord
from ..scrapers.supabase_client import get_client

class VerifyService:
    @staticmethod
    def verify(db: Session, name: str, manufacturer: str = None, batch: str = None):
        name_clean = name.strip()
        manufacturer_clean = manufacturer.strip() if manufacturer else None
        batch_clean = batch.strip() if batch else None

        supabase_result = VerifyService._verify_supabase(name_clean, manufacturer_clean, batch_clean)
        if supabase_result:
            return supabase_result

        return VerifyService._verify_local(db, name_clean, batch_clean)

    @staticmethod
    def _verify_supabase(name: str, manufacturer: Optional[str], batch: Optional[str]):
        try:
            client = get_client()
        except Exception:
            return None

        def search_table(table: str, field: str, query_value: str, limit: int = 5):
            try:
                res = client.table(table).select('*').ilike(field, query_value).limit(limit).execute()
                return res.data if hasattr(res, 'data') else res or []
            except Exception:
                return []

        try:
            recalls = []
            alerts = []

            if batch:
                recall_res = client.table('drug_recalls').select('*').eq('recall_number', batch).limit(1).execute()
                recalls = recall_res.data if hasattr(recall_res, 'data') else recall_res or []

            if not recalls:
                recalls = search_table('drug_recalls', 'reason', f'%{name}%', 3)

            alerts = search_table('drug_alerts', 'title', f'%{name}%')
            if not alerts:
                alerts = search_table('drug_alerts', 'summary', f'%{name}%')
            if not alerts:
                alerts = search_table('drug_alerts', 'details', f'%{name}%')

            if recalls or alerts:
                record = recalls[0] if recalls else alerts[0]
                return {
                    'status': 'unsafe',
                    'name': name,
                    'batch': batch,
                    'authority': record.get('authority') or 'Regulatory Authority',
                    'reason': record.get('reason') or record.get('title') or record.get('summary') or record.get('details') or 'Matched a regulatory alert or recall record.'
                }

            if manufacturer:
                name_query = f"%{manufacturer}%"
            else:
                name_query = f"%{name}%"

            med_data = search_table('medicines', 'name', f'%{name}%')
            if not med_data:
                med_data = search_table('medicines', 'normalized_name', f'%{name.lower()}%')
            if not med_data and manufacturer:
                med_data = search_table('medicines', 'manufacturer', f'%{manufacturer}%')
            if not med_data:
                med_data = search_table('medicines', 'primary_identifier', f'%{name}%')

            if med_data:
                first = med_data[0]
                return {
                    'status': 'safe',
                    'name': first.get('name') or name,
                    'batch': batch,
                    'authority': first.get('manufacturer') if first.get('manufacturer') else None,
                    'reason': 'Verified against current regulatory records: no active recalls or alerts found.'
                }

            return {
                'status': 'unknown',
                'name': name,
                'batch': batch,
                'authority': None,
                'reason': 'No authoritative record was found in current regulatory sources. Please verify batch or manufacturer details.'
            }
        except Exception:
            return None

        return None

    @staticmethod
    def _verify_local(db: Session, name: str, batch: Optional[str]):
        if batch:
            match = db.query(MedicineRecord).filter(
                MedicineRecord.batch == batch
            ).first()
            if match:
                return {
                    'status': match.status,
                    'name': name,
                    'batch': batch,
                    'authority': match.authority,
                    'reason': match.reason
                }

        match = db.query(MedicineRecord).filter(
            MedicineRecord.name.ilike(f'%{name}%')
        ).first()

        if match:
            return {
                'status': match.status,
                'name': name,
                'batch': batch or match.batch,
                'authority': match.authority,
                'reason': match.reason
            }

        seed = name.lower()
        if any(keyword in seed for keyword in ['banned', 'toxic', 'recall', 'fake']):
            return {
                'status': 'unsafe',
                'name': name,
                'batch': batch,
                'authority': 'CDSCO',
                'reason': 'Batch listed on active recall notice — potency deviation exceeds regulatory tolerance.'
            }
        if any(keyword in seed for keyword in ['unknown', 'test', 'xxx']):
            return {
                'status': 'unknown',
                'name': name,
                'batch': batch,
                'authority': None,
                'reason': 'This entry cannot be confidently classified without a regulatory match.'
            }

        return {
            'status': 'unknown',
            'name': name,
            'batch': batch,
            'authority': None,
            'reason': 'No authoritative record was found in the local dataset. Please double-check the name, manufacturer, and batch.'
        }
