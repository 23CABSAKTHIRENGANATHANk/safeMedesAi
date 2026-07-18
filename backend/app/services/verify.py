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

        local_result = VerifyService._verify_local(db, name_clean, batch_clean)
        if local_result and local_result.get("status") != "unknown":
            return local_result

        if manufacturer_clean:
            manufacturer_result = VerifyService._verify_local_by_manufacturer(db, manufacturer_clean)
            if manufacturer_result:
                return manufacturer_result

        return local_result

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

            # ── Batch lookup (most specific) ──────────────────────────────────
            if batch:
                recall_res = client.table('drug_recalls').select('*').eq('recall_number', batch).limit(1).execute()
                recalls = recall_res.data if hasattr(recall_res, 'data') else []

            # ── Recall search: search against reason field (no affected_medicine column) ──
            if not recalls:
                recalls = search_table('drug_recalls', 'reason', f'%{name}%', 3)

            # ── Alert search: title → summary → details ───────────────────────
            # Important: only flag UNSAFE if the alert title clearly matches the drug name,
            # not just a substring in a multi-drug description.
            alerts = search_table('drug_alerts', 'title', f'%{name}%')
            if not alerts:
                alerts = search_table('drug_alerts', 'summary', f'%{name}%')
            if not alerts:
                alerts = search_table('drug_alerts', 'details', f'%{name}%')

            # ── UNSAFE / WARNING: drug found in recalls or alerts ──────────────
            if recalls or alerts:
                record = recalls[0] if recalls else alerts[0]
                # Double-check that the alert title really is about THIS drug (not just mentions it)
                if alerts and not recalls:
                    alert_title = (record.get('title') or '').lower()
                    name_lower = name.lower()
                    # Skip OCR blobs - only count alerts where name is clearly in title
                    if name_lower not in alert_title and len(alert_title) > 200:
                        # The match is buried in a large OCR blob — treat as unknown, not unsafe
                        alerts = []

                if recalls or alerts:
                    record = recalls[0] if recalls else alerts[0]
                    alert_title = (record.get('title') or record.get('reason') or '').lower()
                    alert_summary = (record.get('summary') or record.get('reason') or '').lower()

                    # Determine if this is about a counterfeit/falsified version vs the drug itself
                    counterfeit_keywords = [
                        'falsified', 'counterfeit', 'spurious', 'fake', 'adulterated',
                        'substandard', 'unauthorized', 'without an approved'
                    ]
                    is_counterfeit_alert = any(
                        kw in alert_title or kw in alert_summary
                        for kw in counterfeit_keywords
                    )

                    reason_text = (
                        record.get('reason')
                        or record.get('title')
                        or record.get('summary')
                        or record.get('details')
                        or 'Matched a regulatory alert or recall record.'
                    )

                    if is_counterfeit_alert:
                        # The medicine itself is fine, but a fake version exists
                        return {
                            'status': 'warning',
                            'name': name,
                            'batch': batch,
                            'authority': record.get('authority') or 'Regulatory Authority',
                            'reason': (
                                f'CAUTION: A falsified/counterfeit version of this medicine '
                                f'has been detected. Buy only from licensed pharmacies. '
                                f'Alert detail: {reason_text[:200]}'
                            )
                        }
                    else:
                        return {
                            'status': 'unsafe',
                            'name': name,
                            'batch': batch,
                            'authority': record.get('authority') or 'Regulatory Authority',
                            'reason': reason_text
                        }

            # ── Medicine lookup: try multiple field strategies ─────────────────
            med_data = search_table('medicines', 'name', f'%{name}%')
            if not med_data:
                # Try normalized_name (lowercase)
                med_data = search_table('medicines', 'normalized_name', f'%{name.lower()}%')

            if med_data:
                first = med_data[0]
                return {
                    'status': 'safe',
                    'name': first.get('name') or name,
                    'batch': batch,
                    'authority': 'CDSCO / US FDA / WHO GSMS',
                    'reason': 'Verified against current regulatory records: no active recalls or alerts found.'
                }

            # ── Unknown: not found anywhere ───────────────────────────────────
            return {
                'status': 'unknown',
                'name': name,
                'batch': batch,
                'authority': None,
                'reason': (
                    'No authoritative record was found in current regulatory sources. '
                    'Please verify the medicine name, manufacturer, and batch number. '
                    'If you believe this is a valid medicine, consult your pharmacist.'
                )
            }
        except Exception:
            return None

    @staticmethod
    def _verify_local(db: Session, name: str, batch: Optional[str]):
        """Fallback local SQLite database lookup."""
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

        # Keyword heuristic only as absolute last resort
        seed = name.lower()
        if any(keyword in seed for keyword in ['banned', 'toxic', 'recall', 'fake', 'counterfeit', 'spurious']):
            return {
                'status': 'unsafe',
                'name': name,
                'batch': batch,
                'authority': 'CDSCO',
                'reason': 'Name contains regulatory warning keywords — classified as unsafe by heuristic.'
            }

        return {
            'status': 'unknown',
            'name': name,
            'batch': batch,
            'authority': None,
            'reason': (
                'No authoritative record was found. '
                'Please double-check the medicine name, manufacturer, and batch.'
            )
        }

    @staticmethod
    def _verify_local_by_manufacturer(db: Session, manufacturer: str):
        match = db.query(MedicineRecord).filter(
            MedicineRecord.manufacturer.ilike(f'%{manufacturer}%')
        ).first()
        if match:
            return {
                'status': match.status,
                'name': match.name,
                'batch': match.batch,
                'authority': match.authority,
                'reason': f'Matched manufacturer data: {match.reason}',
            }
        return None
